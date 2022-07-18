# from pickle import TRUE
# from xml.etree.ElementTree import PI
from kivy.app import App
from kivy.config import Config
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.properties import ObjectProperty
from picamera import PiCamera
from picamera.array import PiRGBArray
from threading import Thread
import cups
import time
import cv2
import numpy as np
import math
from gpiozero import Button
from enum import Enum

class State(Enum):
    START = 0
    IDLE = 1
    EFFECT = 2
    SECOND_PRINT = 3
    DONE = 4
    NO_PAPER_OR_INK = 5

class MainView(FloatLayout):

    myText = StringProperty()
    camera_thread = None
    capture_thread = None
    undisort_thread = None
    secondPrint_thread = None
    stop_second_print_thread = False
    distortionVars = None
    piCam = None
    running = True
    currentImg = 0
    lastImages  = [None, None, None]
    lastImage = None
    picRes = (4000,2912)
    picSmallRes = (1650,1120)
    prewRes = (1504,1024)
    #videoRes = (752,512)
    videoRes = (1280,960)
    overlay = None
    alpha_mask = None
    alpha_channel = None
    state = State.IDLE
    cups_conn = None
    first_print = False

    # update image with video resolution
    def update_texture(self,frame):
        frame=cv2.flip(self.video_data,-1)
        buffer=frame.tobytes()
        texture1=Texture.create(size=self.videoRes, colorfmt="rgb")
        texture1.blit_buffer(buffer, colorfmt='rgb', bufferfmt='ubyte')
        self.ids['img'].texture=texture1

    # update view with last image resolution
    def update_textureLastImage(self,frame):
        resized = cv2.resize(self.lastImage, self.prewRes, interpolation = cv2.INTER_AREA)
        frame = cv2.flip(resized,0)
        # Convert to from BGR to RGB
        frame_rgb = frame[...,::-1].copy()
        buffer=frame_rgb.tobytes()
        texture1=Texture.create(size=self.prewRes, colorfmt="rgb")
        texture1.blit_buffer(buffer, colorfmt='rgb', bufferfmt='ubyte')
        self.ids['img'].texture=texture1

    # read from viedo port and update view
    def camera_process(self):
        self.piCam.resolution = self.videoRes
        rawcapture=PiRGBArray(self.piCam)

        for frame in self.piCam.capture_continuous(rawcapture,format="rgb",use_video_port=True):
            frame_array = rawcapture.array
            self.video_data=frame_array
            Clock.schedule_once(self.update_texture)
            rawcapture.truncate(0)
            if(not self.running):
                break

        self.piCam.resolution = self.picRes

    # create instance of buttons and register all
    def init_buttons(self):
        self.blackBtn = Button(2)
        self.greenBtn = Button(4)
        self.redBtn = Button(3)
        self.reg_buttons(State.START)
        #self.reg_buttons(State.IDLE)

    # Register interrupts of all buttons
    def reg_buttons(self, state):
        self.myText = ''
        if state == State.START:
            self.myText = 'Bitte Hintergund wählen'
            self.start_cam_thread()
            self.blackBtn.when_pressed = self.on_Toni
            self.redBtn.when_pressed = self.on_Ulli
            self.ids['box_black'].size_hint = (0.2, 0.25)
            self.ids['text_black'].text = 'Toni'
            self.ids['box_red'].size_hint = (0.2, 0.25)
            self.ids['text_red'].text = 'Ulli'
        elif state == State.IDLE:
            self.first_print = True
            #self.start_cam_thread()
            self.greenBtn.when_pressed = self.on_green
            self.ids['box_green'].size_hint = (0.2, 0.25)
            self.ids['text_green'].text = 'Start'
        elif state == State.EFFECT:
            self.blackBtn.when_pressed = self.on_black
            self.greenBtn.when_pressed = self.on_green
            self.redBtn.when_pressed = self.on_red
            self.ids['box_black'].size_hint = (0.2, 0.25)
            self.ids['text_black'].text = '<-'
            self.ids['box_green'].size_hint = (0.2, 0.25)
            self.ids['text_green'].text = 'Ok'
            self.ids['box_red'].size_hint = (0.2, 0.25)
            self.ids['text_red'].text = '->'
        elif state == State.SECOND_PRINT:
            self.start_secondPrint_thread(90)
            self.blackBtn.when_pressed = self.on_black
            self.greenBtn.when_pressed = self.on_green
            self.ids['box_black'].size_hint = (0.2, 0.25)
            self.ids['text_black'].font_size = '30sp'
            self.ids['text_black'].text = '2. Ausdruck'
            self.ids['box_green'].size_hint = (0.2, 0.25)
            self.ids['text_green'].text = 'Start'
        elif state == State.DONE:
            self.start_secondPrint_thread(30)
            self.greenBtn.when_pressed = self.on_green
            self.ids['box_green'].size_hint = (0.2, 0.25)
            self.ids['text_green'].text = 'Start'
        elif state == State.NO_PAPER_OR_INK:
            self.myText = 'Papier und/oder\nTinte überprüfen'
            self.redBtn.when_pressed = self.on_red
            self.ids['box_red'].size_hint = (0.2, 0.25)
            self.ids['text_red'].font_size = '30sp'
            self.ids['text_red'].text = 'Erledigt'

    # Unregister interrupts of all buttons
    def unreg_buttons(self):
        self.blackBtn.when_pressed = None
        self.greenBtn.when_pressed = None
        self.redBtn.when_pressed = None
        self.ids['box_black'].size_hint = (None, 0)
        self.ids['text_black'].font_size = '50sp'
        self.ids['text_black'].text = ''
        self.ids['box_green'].size_hint = (None, 0)
        self.ids['text_green'].font_size = '50sp'
        self.ids['text_green'].text = ''
        self.ids['box_red'].size_hint = (None, 0)
        self.ids['text_red'].font_size = '50sp'
        self.ids['text_red'].text = ''

    def on_Toni(self):
        self.unreg_buttons()
        self.create_overlay('overlay_Toni.png')
        self.reg_buttons(State.IDLE)

    def on_Ulli(self):
        self.unreg_buttons()
        self.create_overlay('overlay_Ulli.png')
        self.reg_buttons(State.IDLE)

    def on_black(self):
        self.unreg_buttons()
        self.stop_second_print_thread = True
        if self.camera_thread is None:
            self.secondPrint_thread.join()
        self.printPhoto(self.fileName)

    def on_green(self):
        self.unreg_buttons()
        self.stop_second_print_thread = True
        if self.camera_thread is None:
            self.secondPrint_thread.join()
        if self.camera_thread is None or not self.camera_thread.isAlive:
            self.start_cam_thread()
        self.start_capture_thread()

    def on_red(self):
        self.unreg_buttons()
        self.start_red = time.perf_counter()
        self.redBtn.when_released  = self.on_red_release

    def on_red_release(self):
        self.redBtn.when_released = None
        stop = time.perf_counter()
        if stop - self.start_red > 3:
            self.myText = ''
            if self.first_print:
                self.first_print = False
                self.reg_buttons(State.SECOND_PRINT)
            else:
                self.reg_buttons(State.IDLE)
        else:
            self.reg_buttons(State.NO_PAPER_OR_INK)

    # create camera thread
    def start_cam_thread(self):
        self.running = True
        self.camera_thread=Thread(name="camera",target=self.camera_process)
        self.camera_thread.setDaemon(True)
        self.camera_thread.start()

    # create capture thread
    def start_capture_thread(self):
        self.currentImg = 0
        self.capture_thread=Thread(target=self.capture_photos)
        self.capture_thread.setDaemon(True)
        self.capture_thread.start()

    # create undistort image thread
    def start_undistort_thread(self, image, number):
        if self.undisort_thread is not None:
            self.undisort_thread.join()
        self.undisort_thread=Thread(name="undistort",target=self.undistortImage, args=(image,number,))
        self.undisort_thread.setDaemon(True)
        self.undisort_thread.start()

    # create collage thread
    def start_secondPrint_thread(self, sleeptime):
        self.stop_second_print_thread = False
        self.secondPrint_thread=Thread(name="second_print",target=self.wait_for_second_print, args=(sleeptime,))
        self.secondPrint_thread.setDaemon(True)
        self.secondPrint_thread.start()

    # timer for second print
    def wait_for_second_print(self, sleeptime):
        wait = sleeptime
        while wait > 0:
            self.ids['text_black'].text = '2. Ausdruck\n('+str(wait)+' Sek)'
            time.sleep(1)
            wait -= 1
            if self.stop_second_print_thread:
                self.stop_second_print_thread = False
                return

        self.unreg_buttons()
        self.reg_buttons(State.IDLE)

    # capture 3 photos
    def capture_photos(self):
        while self.currentImg <= 2:
            num_of_secs = 5
            output = np.empty((self.picRes[1], self.picRes[0], 3), dtype=np.uint8)

            self.myText = str(num_of_secs)

            while num_of_secs:
                time.sleep(1)
                num_of_secs -= 1
                if num_of_secs == 0:
                    self.myText = 'Cheese'
                else:
                    self.myText = str(num_of_secs)
                if num_of_secs == 0:
                    self.running = False #freeze preview

            self.camera_thread.join()

            self.piCam.capture(output,format='bgr')

            self.lastImage = output

            Clock.schedule_once(self.update_textureLastImage)

            self.start_undistort_thread(self.lastImage, self.currentImg)

            self.currentImg += 1

            time.sleep(2)

            if self.currentImg <= 2:
                self.start_cam_thread()

        if self.undisort_thread is not None:
            self.undisort_thread.join()

        self.create_collage()

    # create Collage
    def create_collage(self):
        self.myText = 'Bitte warten'

        resized = [None, None, None]

        resized[0] = cv2.resize(self.lastImages[0], self.picSmallRes, interpolation = cv2.INTER_AREA)
        resized[1] = cv2.resize(self.lastImages[1], self.picSmallRes, interpolation = cv2.INTER_AREA)
        resized[2] = cv2.resize(self.lastImages[2], self.picSmallRes, interpolation = cv2.INTER_AREA)
        resized[2] = cv2.resize(self.lastImages[2], self.picSmallRes, interpolation = cv2.INTER_AREA)

        # Crate collage
        resized[0] = cv2.copyMakeBorder(resized[0],82, 82, 121, 121, cv2.BORDER_CONSTANT)
        resized[1] = cv2.copyMakeBorder(resized[1],82, 82, 121, 121, cv2.BORDER_CONSTANT)
        resized[2] = self.rotation(resized[2],15)
        resized[2] = resized[2][:,:(resized[2].shape[1]-89),:]
        resized[2] = cv2.copyMakeBorder(resized[2],530, 530, 99, 0, cv2.BORDER_CONSTANT)
        horizontal = np.vstack([resized[0],resized[1]])
        final = np.hstack([resized[2],horizontal])

        # Apply overlay
        composite = final * self.alpha_mask + self.overlay
        final[:,:,:] = composite

        # Show Collage
        self.lastImage = final
        Clock.schedule_once(self.update_textureLastImage)

        self.fileName = self.saveImage(final, True)

        self.printPhoto(self.fileName)

    def undistortImage(self, image, number):
        if(number >= 0 and number <= 2):
            dst = cv2.undistort(image,self.mtx,self.dist,None,self.newcameramtx)
            x,y,w,h = self.roi
            self.lastImages[number] = dst[y:y+h, x:x+w]
            self.saveImage(self.lastImages[number])

    # save image with timestamp to file
    def saveImage(self, image, print=False):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        if print:
            filename = "/home/pi/Fotobox/fotos/prints/IMG_{}.jpeg".format(timestamp)
        else:
            filename = "/home/pi/Fotobox/fotos/IMG_{}.jpeg".format(timestamp)

        cv2.imwrite(filename,image)

        return filename

    def printPhoto(self,fileName):
        self.myText = 'Foto wird gedruckt'
        for job in self.cups_conn.getJobs():
            print('Lösche Job: ' + str(job))
            self.cups_conn.cancelJob(job, purge_job=False)
        printers = self.cups_conn.getPrinters()
        default_printer = 'Canon_SELPHY_CP1300'
        self.cups_conn.enablePrinter(default_printer)
        cups.setUser('pi')
        print('Drucke File ' + fileName)
        current_job = self.cups_conn.printFile (default_printer, fileName, "Mein Ausdruck", {'fit-to-page':'True','StpBorderless':'True','StpiShrinkOutput':'Expand'})
        # current_job = 0
        time.sleep(2)

        printers = self.cups_conn.getPrinters()
        message = printers[default_printer]['printer-state-message']
        notReady = 'Ink' in message or 'Paper' in message
        if notReady:
            print(str(notReady) + ' mit ID ' + str(current_job))
            time.sleep(1)
            for job in self.cups_conn.getJobs():
                print('Lösche Job: ' + str(job))
                self.cups_conn.cancelJob(job, purge_job=False)
            self.cups_conn.enablePrinter(default_printer)
            self.reg_buttons(State.NO_PAPER_OR_INK)
        else:
            wait = 60
            while wait > 0:
                self.myText = 'Foto wird gedruckt (' + str(wait) + ' Sek)'
                time.sleep(1)
                wait -= 1
            if self.first_print:
                self.first_print = False
                self.reg_buttons(State.SECOND_PRINT)
            else:
                self.reg_buttons(State.DONE)

    # rotate image
    def rotation(self, image, angleInDegrees):
        h, w = image.shape[:2]
        img_c = (w / 2, h / 2)

        rot = cv2.getRotationMatrix2D(img_c, angleInDegrees, 1)

        rad = math.radians(angleInDegrees)
        sin = math.sin(rad)
        cos = math.cos(rad)
        b_w = int((h * abs(sin)) + (w * abs(cos)))
        b_h = int((h * abs(cos)) + (w * abs(sin)))

        rot[0, 2] += ((b_w / 2) - img_c[0])
        rot[1, 2] += ((b_h / 2) - img_c[1])

        outImg = cv2.warpAffine(image, rot, (b_w, b_h), flags=cv2.INTER_LINEAR)
        return outImg

    # create overlay mask
    def create_overlay(self, filePath):
        foreground = cv2.imread(filePath,-1)

        foreground_colors = foreground[:, :, :3]
        self.alpha_channel = foreground[:, :, 3] / 255  # 0-255 => 0.0-1.0

        self.alpha_mask = np.dstack((self.alpha_channel, self.alpha_channel, self.alpha_channel))
        self.overlay = foreground_colors[:,:,:]
        overlay = foreground_colors * self.alpha_mask
        self.overlay[:,:,:] = overlay
        self.alpha_mask = (1-self.alpha_mask)

class PhotoboxApp(App):
    def build(self):
        Config.set("graphics", "show_cursor", 0)
        layout = MainView()
        layout.piCam=PiCamera()
        layout.init_buttons()
        layout.distortionVars = np.load('picamCalibration.npz')
        layout.mtx = layout.distortionVars['mtx']
        layout.dist = layout.distortionVars['dist']
        layout.cups_conn = cups.Connection()
        w = layout.picRes[0]
        h = layout.picRes[1]
        layout.newcameramtx, layout.roi = cv2.getOptimalNewCameraMatrix(layout.mtx,layout.dist,(w,h),1,(w,h))

        # Overlay mask
        # foreground = cv2.imread('overlay.png',-1)

        # foreground_colors = foreground[:, :, :3]
        # layout.alpha_channel = foreground[:, :, 3] / 255  # 0-255 => 0.0-1.0

        # layout.alpha_mask = np.dstack((layout.alpha_channel, layout.alpha_channel, layout.alpha_channel))
        # layout.overlay = foreground_colors[:,:,:]
        # overlay = foreground_colors * layout.alpha_mask
        # layout.overlay[:,:,:] = overlay
        # layout.alpha_mask = (1-layout.alpha_mask)

        layout.create_overlay('overlay.png')

        return layout


if __name__ == '__main__':
    PhotoboxApp().run()


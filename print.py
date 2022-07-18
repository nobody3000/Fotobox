import cups
import time

conn = cups.Connection()
printers = conn.getPrinters()
default_printer = 'Canon_SELPHY_CP1300'
cups.setUser('pi')
fileName = '/home/pi/fotobox/fotos/IMG_20220308_212909.jpeg'
printerUri = printers[default_printer]['printer-uri-supported']
print(printerUri)
print(conn.getJobs())
for job in conn.getJobs():
    conn.cancelJob(job, purge_job=False)
# conn.cancelJob(711, purge_job=False)
# conn.enablePrinter(default_printer)
# conn.cancelAllJobs(printerUri)

# current_job = conn.printFile (default_printer, fileName, "Mein Ausdruck", {'fit-to-page':'True','StpBorderless':'True','StpiShrinkOutput':'Expand'})
# conn.getJobAttributes(current_job)["job-state"]
# time.sleep(2)
# #  conn.enablePrinter(default_printer)
# #  conn.disablePrinter(default_printer)


# printers = conn.getPrinters()
# message = printers[default_printer]['printer-state-message']
# notReady = 'Ink' in message or 'Paper' in message
# if notReady:
#     print('Canceled')
#     conn.cancelJob(current_job, purge_job=False)
#     time.sleep(1)
#     # self.myText = 'Papier und/oder Tinte überprüfen'
#     conn.enablePrinter(default_printer)
# else:
#     jobState = conn.getJobAttributes(current_job)["job-state"]
#     while jobState is not 9:
#         time.sleep(2)
#         jobState = conn.getJobAttributes(current_job)["job-state"]
#         print(jobState)
    



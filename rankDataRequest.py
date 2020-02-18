# rankDataRequest.py

import blpapi
import sys
import datetime

SESSION_STARTED                 = blpapi.Name("SessionStarted")
SESSION_STARTUP_FAILURE         = blpapi.Name("SessionStartupFailure")
SESSION_CONNECTION_UP           = blpapi.Name("SessionnConnectionUp")
SESSION_CONNECTION_DOWN         = blpapi.Name("SessionConnectionDown")
SESSION_TERMINATED              = blpapi.Name("SessionTerminated")

SERVICE_OPENED                  = blpapi.Name("ServiceOpened")
SERVICE_OPEN_FAILURE            = blpapi.Name("ServiceOpenFailure")

#SLOW_CONSUMER_WARNING           = blpapi.Name("SlowConsumerWarning")
#SLOW_CONSUMER_WARNING_CLEARED   = blpapi.Name("SlowConsumerWarningCleared")

ERROR_INFO                      = blpapi.Name("ErrorInfo")
GET_RANK_DATA_RESPONSE          = blpapi.Name("GetRankDataResponse")

# desktop authentication
# beta service
d_service="//blp/rankapi-beta"
# prod service
#d_service="//blp/rankapi"

d_host="localhost"
d_port=8194
bEnd=False

class SessionEventHandler():

    # start of create new rank request
    def processEvent(self, event, session):
        try:
            
            if event.eventType() == blpapi.Event.ADMIN:
                self.processAdminEvents(event)

            elif event.eventType() == blpapi.Event.SESSION_STATUS:
                self.processSessionStatusEvent(event,session)
                        
            elif event.eventType() == blpapi.Event.SERVICE_STATUS:
                self.processServiceStatusEvent(event,session)
            
            elif event.eventType() == blpapi.Event.RESPONSE:
                self.processResposeEvent(event)
            
            elif event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                self.processPartialResponseEvent(event)
            
            else:
                self.processMiscEvents(event)
        
        except:
            print ("Exception: %s" % sys.exc_info()[0])
        
        return False

    # only relevant for subscription service
    # def processAdminEvents(self, event):
    #         print ("Processing ADMIN event")

    #         for msg in event:
    #             if msg.messageType() == SLOW_CONSUMER_WARNING:
    #                 print ("Warning: Entered Slow Consumer status")

    #             elif msg.messageType() == SLOW_CONSUMER_WARNING_CLEARED:
    #                 sys.stderr.write("Slow Consumer status cleared")
                
    #             else:
    #                 print(msg)                 
    

    def processSessionStatusEvent(self, event, session):
        print("Processing SESSION_STATUS event")

        for msg in event:
            if msg.messageType() == SESSION_STARTED:
                print ("Session started...")
                session.openServiceAsync(d_service)
            
            elif msg.messageType() == SESSION_STARTUP_FAILURE:
                print >> sys.stderr, ("Error: Session startup failed")
            
            elif msg.messageType() == SESSION_TERMINATED:
                print ("Error: Session has been terminated")
            
            elif msg.messageType() == SESSION_CONNECTION_UP:
                print ("Session connection is up")
            
            elif msg.messageType() == SESSION_CONNECTION_DOWN:
                print ("Session connection is down")
            
            else:
                print (msg)
    

    def processServiceStatusEvent(self, event, session):
        print ("Processing SERVICE_STATUS event")

        for msg in event:

            if msg.messageType() == SERVICE_OPENED:
                print ("Service opened...")

                service = session.getService(d_service)

                # build request
                request = service.createRequest("Query")

                request.set("Query")

                brokers = request.getElement("brokers")
                
                #brokers.setChoice("acronym")
                #brokers.setChoice("name")
                #brokers.setChoice("rank")

                #brokers.setElement("acronym", "") 
                #brokers.setElement("name", "")
                #brokers.setElement("rank", ) 

                # set date
                request.set("start", datetime.datetime(2020, 1, 1, 0, 0, 0, 0)) # 2020-Jan-01
                request.set("end", datetime.datetime(2020, 1, 9, 0, 0, 0, 0)) # 2020-Jan-09
                
                # group by  0= , 1=
                request.set("groupBy","")
                
                # securities or exchanges
                SecurityCriteria = request.getElement("SecurityCriteria")
                SecurityCriteria.setChoice("securities")
                # SecurityCriteria.setChoice("exchanges")

                Security = request.getElement("Security")
                Security.setChoice("ticker").appendValue("AAPL US Equity")
                # Security.setchoice("figi").appendvalue("ABC1234")


                # enumerationType Source 0=Broker 1=Security
                request.getElement("Source").appendValue(1)   

                # enumerationType 0=Shares, 1=Local, 2=USD, 3=EUR, 4=GBP
                request.getElement("Units").appendValue("1")



                print ("Request: %s" % request.toString())

                self.requestID = blpapi.CorrelationId()

                session.sendRequest(request, correlationID=self.requestID)

            elif msg.messageType() == SERVICE_OPEN_FAILURE:
                print >> sys.stderr, ("Error: Service failed to open")
    

    def processResponseEvent(self, event):
        print ("Processing RESPONSE event")

        for msg in event:

            if msg.correlationIds()[0].value() == self.requestID.value():
                print ("MESSAGE TYPE: %s" % msg.messageType())

                if msg.messageType() == ERROR_INFO:
                    errorCode = msg.getElementAsInteger("ERROR_CODE")
                    errorMessage = msg.getElementAsString("ERROR_MESSAGE")
                    print ("ERROR CODE: %d\tERROR MESSAGE: %s" % (errorCode, errorMessage))
                elif msg.messageType() == GET_RANK_DATA_RESPONSE:

                    print(msg)

                    # rankData = msg.getElement("rankDataResponse")
                    # for rankData in rankData.values():
                    #        columnns = 

                    
            global bEnd
            bEnd = True


    def processMiscEvents(self, event):

        print ("Processing " + event.eventType() + " event")

        for msg in event:

            print ("MESSAGE: %s" % (msg.toString()))


def main():

    

    sessionOptions = blpapi.SessionOptions()
    sessionOptions.setServerHost(d_host)
    sessionOptions.setServerPort(d_port)

    print ("Connecting to %s:%d" % (d_host, d_port))

    eventHandler = SessionEventHandler()

    session = blpapi.Session(sessionOptions, eventHandler.processEvent)

    if not session.startAsync():
        print ("Failed to start session.")
        return

    global bEnd
    while bEnd==False:
        pass
    
    session.stop()

if __name__ == "__main__":
    print ("Bloomberg - RANK API Example - rankDataRequst")
    try:
        main()
    except KeyboardInterrupt:
        print ("Ctrl+C pressed. Stopping...")


__copyright__ = """
Copyright 2017. Bloomberg Finance L.P.
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:  The above
copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""






# rankDataRequest.py

import blpapi
import sys
import datetime
import os

# for additional DEBUG logging
#os.environ['BLPAPI_LOGLEVEL'] = 'DEBUG'

SESSION_STARTED                 = blpapi.Name("SessionStarted")
SESSION_STARTUP_FAILURE         = blpapi.Name("SessionStartupFailure")
SESSION_CONNECTION_UP           = blpapi.Name("SessionnConnectionUp")
SESSION_CONNECTION_DOWN         = blpapi.Name("SessionConnectionDown")
SESSION_TERMINATED              = blpapi.Name("SessionTerminated")

SERVICE_OPENED                  = blpapi.Name("ServiceOpened")
SERVICE_OPEN_FAILURE            = blpapi.Name("ServiceOpenFailure")

SLOW_CONSUMER_WARNING           = blpapi.Name("SlowConsumerWarning")
SLOW_CONSUMER_WARNING_CLEARED   = blpapi.Name("SlowConsumerWarningCleared")

ERROR_INFO                      = blpapi.Name("ErrorInfo")
REPORT                          = blpapi.Name("Report")
  
# desktop authentication
# beta service
d_service="//blp/rankapi-beta"

# prod service
#d_service="//blp/rankapi"

d_host="localhost"
d_port=8194

bEnd=False

class SessionEventHandler():

    def processEvent(self, event, session):
        try:
            if event.eventType() == blpapi.Event.SESSION_STATUS:
                self.processSessionStatusEvent(event,session)
            
            elif event.eventType() == blpapi.Event.SERVICE_STATUS:
                self.processServiceStatusEvent(event,session)

            elif event.eventType() == blpapi.Event.RESPONSE or event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                self.processResponseEvent(event)
            
            else:
                self.processMiscEvents(event)
                
        except:
            print ("Exception:  %s" % sys.exc_info()[0])
            
        return False

    # only relevant for subscription service
    def processAdminEvents(self, event):
            print ("Processing ADMIN event")

            for msg in event:
                if msg.messageType() == SLOW_CONSUMER_WARNING:
                    print ("Warning: Entered Slow Consumer status")

                elif msg.messageType() == SLOW_CONSUMER_WARNING_CLEARED:
                    sys.stderr.write("Slow Consumer status cleared")
                
                else:
                    print(msg)                 
    

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
                
                ### specify broker by acronym, name or rank
                #broker = request.getElement("brokers").appendElement()
                #broker.setElement("acronym", "BCAP"); # acronym
                # broker.setElement("rank", 1) # rank of the broker

                ### set date/time range
                request.set("start", datetime.datetime(2020, 1, 1, 0, 0, 0, 0)) 
                request.set("end", datetime.datetime(2020, 5, 5, 0, 0, 0, 0)) 
                            
                ### group by 0=Broker , 1=Security
                #request.set("groupBy", "Broker")
                request.set("groupBy", "Security")

                ### exchanges or securities 
                # exchanges can be set using code 
                #exchanges = request.getElement("securityCriteria").setChoice("exchanges")
                #exchange = exchanges.appendElement()
                #exchange.setElement("code", "US");
            
                ### securities can be set to either Bloomberg ticker or figi
                securities = request.getElement("securityCriteria").setChoice("securities")
                security = securities.appendElement()
                security.setElement("ticker", "AAPL US Equity");
                #security.setElement("figi", "BBG000B9XRY4"); # figi for AAPL US Equity
              
                ### source enum 0=Broker Contributed
                request.set("source", "Broker Contributed")

                ### units enum 0=Shares, 1=Local, 2=USD, 3=EUR, 4=GBP
                request.set("units", "Shares")             
                
                print ("Sending Request: %s" % request.toString())

                #self.requestID = session.sendRequest(request)
                
                self.requestID = blpapi.CorrelationId()
                session.sendRequest(request, correlationId=self.requestID)
                
                print ("RANK data request sent.")

            elif msg.messageType() == SERVICE_OPEN_FAILURE:
                print >> sys.stderr, ("Error: Service failed to open")


    def processResponseEvent(self, event):
        print ("Processing RESPONSE event")

        for msg in event:
            # for printing raw message
            #print(msg)

            if msg.correlationIds()[0].value() == self.requestID.value():
                print ("MESSAGE TYPE: %s" % msg.messageType())

                if msg.messageType() == ERROR_INFO:
                    errorCode = msg.getElementAsInteger("errorCode")
                    errorMessage = msg.getElementAsString("errorMessage")
                    timestampUtc = msg.getElementAsFloat("timestamp Utc")
                    print ("ERROR CODE: %d\tERROR MESSAGE: %s" % (errorCode,errorMessage))    
                
                elif msg.messageType() == REPORT:

                    records = msg.getElement("records")
                    print(records)

                #     for record in records.values():

                #         bought = record.getElement("bought").getValueAsFloat()
                #         broker = record.getElement("broker").getElement("acronym").getValue()
                #         crossed = record.getElement("crossed").getValueAsFloat()
                #         highTouch = record.getElement("highTouch").getValueAsFloat()
                #         lowTouch = record.getElement("lowTouch").getValueAsFloat()
                #         numReports = record.getElement("numReports").getValueAsInteger()
                #         sold = record.getElement("sold").getValueAsFloat()
                #         topBrokers = record.getElement("topBrokers").getElement("acronym").getValue()
                #         #topBrokers = record.getElement("topBrokers").getElement("name").getValue()
                #         #topBrokers = record.getElement("topBrokers").getElement("rank").getValue()
                #         total = record.getElement("total").getValueAsFloat()
                #         traded = record.getElement("traded").getValueAsFloat()

                #         print ("Bought: %f\tBroker: %s\tCrossed: %f" % (bought, broker, crossed))
                #         print ("numReports %d\ttopBroker: %s\ttotal: %f\ttraded: %f" % (numReports, topBrokers, total, traded))     
                # global bEnd
                # bEnd = True    
                        

    def processMiscEvents(self, event):
        print ("Processing " + event.eventType() + " event")

        for msg in event:

            print ("MESSAGE: %s" % (msg.toString()))


def main():

    sessionOptions = blpapi.SessionOptions()
    sessionOptions.setServerHost(d_host)
    sessionOptions.setServerPort(d_port)
    sessionOptions.setMaxPendingRequests(1)
    
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
Copyright 2020. Bloomberg Finance L.P.
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






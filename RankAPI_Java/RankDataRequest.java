/* Copyright 2020. Bloomberg Finance L.P.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to
 * deal in the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:  The above
 * copyright notice and this permission notice shall be included in all copies
 * or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */
package com.bloomberg.emsx.samples;

import com.bloomberglp.blpapi.CorrelationID;
import com.bloomberglp.blpapi.Datetime;
import com.bloomberglp.blpapi.Element;
import com.bloomberglp.blpapi.Event;
import com.bloomberglp.blpapi.EventHandler;
import com.bloomberglp.blpapi.Message;
import com.bloomberglp.blpapi.MessageIterator;
import com.bloomberglp.blpapi.Name;
import com.bloomberglp.blpapi.Request;
import com.bloomberglp.blpapi.Service;
import com.bloomberglp.blpapi.Session;
import com.bloomberglp.blpapi.SessionOptions;


public class RankDataRequest {
	
	private static final Name 	SESSION_STARTED 		= new Name("SessionStarted");
	private static final Name 	SESSION_STARTUP_FAILURE = new Name("SessionStartupFailure");
	private static final Name 	SERVICE_OPENED 			= new Name("ServiceOpened");
	private static final Name 	SERVICE_OPEN_FAILURE 	= new Name("ServiceOpenFailure");
	
    private static final Name 	EXCEPTION = new Name("Exception");
    private static final Name 	REPORT = new Name("Report");

	private String 	d_service;
    private String  d_host;
    private int     d_port;
    
    private CorrelationID requestID;
    
    private static boolean quit=false;
    
    public static void main(String[] args) throws java.lang.Exception
    {
        System.out.println("Bloomberg - RANK API Example - rankDataRequest\n");

        RankDataRequest example = new RankDataRequest();
        example.run(args);

        while(!quit) {
        	Thread.sleep(10);
        };
        
    }
    
    public RankDataRequest()
    {
    	
    	// Define the service required, in this case the EMSX beta service, 
    	// and the values to be used by the SessionOptions object
    	// to identify IP/port of the back-end process.
    	
    	d_service = "//blp/rankapi-beta";
    	d_host = "localhost";
        d_port = 8194;

    }

    private void run(String[] args) throws Exception
    {

    	SessionOptions d_sessionOptions = new SessionOptions();
        d_sessionOptions.setServerHost(d_host);
        d_sessionOptions.setServerPort(d_port);

        Session session = new Session(d_sessionOptions, new RANKEventHandler());
        
        session.startAsync();
        
    }
    
    class RANKEventHandler implements EventHandler
    {
        public void processEvent(Event event, Session session)
        {
            try {
                switch (event.eventType().intValue())
                {                
                case Event.EventType.Constants.SESSION_STATUS:
                    processSessionEvent(event, session);
                    break;
                case Event.EventType.Constants.SERVICE_STATUS:
                    processServiceEvent(event, session);
                    break;
                case Event.EventType.Constants.RESPONSE:
                    processResponseEvent(event, session);
                    break;
                case Event.EventType.Constants.PARTIAL_RESPONSE:
                    processResponseEvent(event, session);
                    break;
                default:
                    processMiscEvents(event, session);
                    break;
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

		private boolean processSessionEvent(Event event, Session session) throws Exception {

			System.out.println("Processing " + event.eventType().toString());
        	
			MessageIterator msgIter = event.messageIterator();
            
			while (msgIter.hasNext()) {
            
				Message msg = msgIter.next();
                
				if(msg.messageType().equals(SESSION_STARTED)) {
                	System.out.println("Session started...");
                	session.openServiceAsync(d_service);
                } else if(msg.messageType().equals(SESSION_STARTUP_FAILURE)) {
                	System.err.println("Error: Session startup failed");
                	return false;
                }
            }
            return true;
		}

        private boolean processServiceEvent(Event event, Session session) {

        	System.out.println("Processing " + event.eventType().toString());
        	
        	MessageIterator msgIter = event.messageIterator();
            
        	while (msgIter.hasNext()) {
            
        		Message msg = msgIter.next();
                
        		if(msg.messageType().equals(SERVICE_OPENED)) {
                
        			System.out.println("Service opened...");
                	
                    Service service = session.getService(d_service);

					// create request
                    Request query = service.createRequest("Query");

					//specify broker by acronym or rank
					Element broker = query.getElement("brokers");
					broker = query.getElement("brokers").appendElement();
					broker.setElement("acronym", "BCAP"); // broker acronym
					
					// set date range
            	    query.set("start", "2020-01-01");
            	    query.set("end", "2020-05-01");
					
					// group by 0=Broker, 1=Security
					query.set("gropuby", "Broker");
					//query.set("groupby", "Security");
					
					// exchanges or securities
					// exchanges can be set using Bloomberg exchange code
					//Element securities = query.getElement("securityCriteria").setChoice("exchanges");
					//Element exchange = securities.appendElement();
					//exchange.getElement("code").setValue("US"); 

					// securities can be set to either Bloomberg ticker or figi
					Element securities = query.getElement("securityCriteria").setChoice("securities");
					Element security = securities.appendElement();
					security.setElement("ticker", "AAPL US Equity");
					//security.setElement("figi", "BBG000B9XRY4"); // figi for AAPL US Equity

					// sources enum 0=Broker Contributed
					query.Set("source", "Broker Contributed");

					// units enum 0=Shares, 1=Local, 2=USD, 3=EUR, 4=GBP
					query.Set("units", "Shares");
					
            	    System.out.println("Request: " + query.toString());

                    requestID = new CorrelationID();
                    
                    // Submit the request
                	try {
                        session.sendRequest(query, requestID);
                	} catch (Exception ex) {
                		System.err.println("Failed to send the request");
                		return false;
                	}
                	
                } else if(msg.messageType().equals(SERVICE_OPEN_FAILURE)) {
                	System.err.println("Error: Service failed to open");
                	return false;
                }
            }
            return true;
		}

		private boolean processResponseEvent(Event event, Session session) throws Exception 
		{
			System.out.println("Received Event: " + event.eventType().toString());
            
            MessageIterator msgIter = event.messageIterator();
            
            while(msgIter.hasNext())
            {
				Message msg = msgIter.next();

				System.out.println("Message: " + msg.toString());
                
                if(event.eventType()==Event.EventType.RESPONSE && msg.correlationID()==requestID) {
                	
                	System.out.println("Message Type: " + msg.messageType());
                	if(msg.messageType().equals(ERROR_INFO)) {
                		Integer errorCode = msg.getElementAsInt32("ErrorCode");
                		String errorMessage = msg.getElementAsString("ErrorMsg");
						System.out.println("ERROR CODE: " + errorCode + "\tERROR MESSAGE: " + errorMessage);
						
                	} else if(msg.messageType().equals(REPORT)) {
                		
						Element records = msg.getElement("records");
						
						int numValues = records.numValues();
                		
						for(int i=0; i<numFills; i++) {
							
							Element record = records.getValueAsElement(i);

							double bought = record..getElementAsFloat64("bought");

							Element broker = record.getElement("broker");

							string acronym = broker.getElemetAsString("acronym");
							//int rank = broker.getElementAsInt32("rank");

							double crossed = record.getElementAsFloat64("crossed");
							double highTouch = record.getElementAsFloat64("highTouch");
							double lowTouch = record.getElementAsFloat64("lowTouch");
							int numReports = record.getElementAsInt32("numReports");
							
							// securities can be set to either Bloomberg ticker or figi
							//Element security = record.getElement("security");
							//string ticker = security.getElementAsString("ticker");
							//string figi = security.getElementAsString("figi");

							double sold = record.getElementAsFloat64("sold");
							double total = record.getElementAsFloat64("total");
							double traded = record.getElementAsFloat64("traded");

							System.out.println("Broker: " + broker);
							//System.out.println("Rank: " + rank);
							//System.out.println("Ticker: " + ticker);
							//System.out.println("Figi: " + figi);	
							System.out.println("Bought: " + bought + "\tCrossed: " + crossed + "\tHigh Touch: " + highTouch + "\tLow Touch: " + lowTouch + 
							"\nNumber of Reports: " + numReports + "\tSold: " + sold + "\tTotal: " +  total + "\tTraded: " = traded);
							
						}
                	}
                	                	
                	quit=true;
                	session.stop();
                }
            }
            return true;
		}
		
        private boolean processMiscEvents(Event event, Session session) throws Exception 
        {
            System.out.println("Processing " + event.eventType().toString());
            MessageIterator msgIter = event.messageIterator();
            while (msgIter.hasNext()) {
                Message msg = msgIter.next();
                System.out.println("MESSAGE: " + msg);
            }
            return true;
        }

    }	
	
}
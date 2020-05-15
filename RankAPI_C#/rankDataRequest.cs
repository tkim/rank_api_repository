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

using Name = Bloomberglp.Blpapi.Name;
using SessionOptions = Bloomberglp.Blpapi.SessionOptions;
using Session = Bloomberglp.Blpapi.Session;
using Service = Bloomberglp.Blpapi.Service;
using Request = Bloomberglp.Blpapi.Request;
using Element = Bloomberglp.Blpapi.Element;
using CorrelationID = Bloomberglp.Blpapi.CorrelationID;
using Event = Bloomberglp.Blpapi.Event;
using Message = Bloomberglp.Blpapi.Message;
using EventHandler = Bloomberglp.Blpapi.EventHandler;
using System;

namespace rankDataRequest
{
    public class RankDataRequest
    {
        private static readonly Name SESSION_STARTED = new Name("SessionStarted");
        private static readonly Name SESSION_STARTUP_FAILURE = new Name("SessionStartupFailure");
        private static readonly Name SERVICE_OPENED = new Name("ServiceOpened");
        private static readonly Name SERVICE_OPEN_FAILURE = new Name("ServiceOpenFailure");

        private static readonly Name EXCEPTION = new Name("Exception");
        private static readonly Name REPORT = new Name("Report");

        private string d_service;
        private string d_host;
        private int d_port;

        private static bool quit = false;

        private CorrelationID requestID;


        public static void Main(String[] args)
        {
            System.Console.WriteLine("Bloomberg - RANK API Example - rankDataRequest\n");

            RankDataRequest example = new RankDataRequest();
            example.run(args);

            while (!quit) { };

            System.Console.WriteLine("Press any key...");
            System.Console.ReadKey();

        }

        public RankDataRequest()
        {
            // Define the service required, in this case the -beta service,
            // and the values to be used by the SessionOptions object
            // to identify IP/port of the back-end process.

            d_service = "//blp/rankapi-beta";
            d_host = "localhost";
            d_port = 8194;

        }

        private void run(String[] args)
        {
            SessionOptions d_sessionOptions = new SessionOptions();
            
            d_sessionOptions.ServerHost = d_host;
            d_sessionOptions.ServerPort = d_port;

            Session session = new Session(d_sessionOptions, new EventHandler(processEvent));

            session.StartAsync();

        }

        public void processEvent(Event evt, Session session)
        {
            try
            {
                switch (evt.Type)
                {
                    case Event.EventType.SESSION_STATUS:
                        processSessionEvent(evt, session);
                        break;
                    case Event.EventType.SERVICE_STATUS:
                        processServiceEvent(evt, session);
                        break;
                    case Event.EventType.RESPONSE:
                        processResponseEvent(evt, session);
                        break;
                    case Event.EventType.PARTIAL_RESPONSE:
                        processResponseEvent(evt, session);
                        break;
                    default:
                        processMiscEvents(evt, session);
                        break;
                }
            }
            catch (Exception e)
            {
                System.Console.Error.WriteLine(e);
            }
        }

        private void processSessionEvent(Event evt, Session session)
        {
            System.Console.WriteLine("\nProcessing " + evt.Type);

            foreach (Message msg in evt)
            {
                if (msg.MessageType.Equals(SESSION_STARTED))
                {
                    System.Console.WriteLine("Session Started...");
                    session.OpenServiceAsync(d_service);
                }
                else if (msg.MessageType.Equals(SESSION_STARTUP_FAILURE))
                {
                    System.Console.Error.WriteLine("Error: Session starup failure");
                }
            }
        }

        private void processServiceEvent(Event evt, Session session)
        {
            System.Console.WriteLine("\nProcessing " + evt.Type);

            foreach (Message msg in evt)
            {
                if (msg.MessageType.Equals(SERVICE_OPENED))
                {
                    System.Console.WriteLine("Service opened...");

                    Service service = session.GetService(d_service);

                    // create request
                    Request query = service.CreateRequest("Query");

                    // specify broker by acronym or rank
                    Element broker = query.GetElement("brokers");
                    broker = query.GetElement("brokers").AppendElement();
                    broker.SetElement("acronym", "BCAP"); // broker acronym

                    // set date range
                    query.Set("start", "2020-01-01");
                    query.Set("end", "2020-04-01");

                    // group by 0=Broker, 1=Security
                    query.Set("groupBy", "Broker");
                    //query.Set("groupBy", "Security");

                    // exchanges or securities
                    // exchanges can be set using Bloomberg exchange code                
                    //Element securities = query.GetElement("securityCriteria").SetChoice("exchanges");
                    //Element exchange = securities.AppendElement();
                    //exchange.GetElement("code").SetValue("US");
         
                    // securities can be set to either Bloomberg ticker or figi
                    Element securities = query.GetElement("securityCriteria").SetChoice("securities");
                    Element security = securities.AppendElement();
                    security.SetElement("ticker", "AAPL US Equity");
                    //security.SetElement("figi", "BBG000B9XRY4"); // figi for AAPL US Equity

                    // sources enum 0=Broker Contributed
                    query.Set("source", "Broker Contributed");

                    // units enum 0=Shares, 1=Local, 2=USD, 3=EUR, 4=GBP
                    query.Set("units", "Shares");

                    System.Console.WriteLine("Request: " + query.ToString());

                    requestID = new CorrelationID();

                    // submit the request
                    try
                    {
                        session.SendRequest(query, requestID);
                    }
                    catch (Exception ex)
                    {
                        System.Console.Error.WriteLine("Failed to send the request: " + ex.Message);
                    }
                }
                else if (msg.MessageType.Equals(SERVICE_OPEN_FAILURE))
                {
                    System.Console.Error.WriteLine("Error: Service failed to open");
                }
            }
        }

        private void processResponseEvent(Event evt, Session session)
        {
            System.Console.WriteLine("Received Event: " + evt.Type);
       

            foreach (Message msg in evt)
            {
                System.Console.WriteLine("Msg: " + msg.ToString());
                if (evt.Type == Event.EventType.RESPONSE && msg.CorrelationID == requestID)
                {
                    System.Console.WriteLine("Message Type: " + msg.MessageType);
                    if (msg.MessageType.Equals(ERROR_INFO))
                    {
                        int errorCode = msg.GetElementAsInt32("ERROR_CODE");
                        String errorMessage = msg.GetElementAsString("ERROR_MESSAGE");
                        System.Console.WriteLine("ERROR CODE: " + errorCode + "\tERROR MESSAGE: " + errorMessage);
                    }
                    else if (msg.MessageType.Equals(REPORT))
                    {
                        Element records = msg.GetElement("records");

                        int numValues = records.NumValues;

                        for (int i = 0; i < numValues; i++)
                        {
                            Element record = records.GetValueAsElement(i);

                            double bought = record.GetElementAsFloat64("bought");

                            Element broker = record.GetElement("broker");

                            string acronym = broker.GetElementAsString("acronym");
                            //int rank = broker.GetElementAsInt32("rank"); 
                      
                            double crossed = record.GetElementAsFloat64("crossed");
                            double highTouch = record.GetElementAsFloat64("highTouch");
                            double lowTouch = record.GetElementAsFloat64("lowTouch");
                            int numReports = record.GetElementAsInt32("numReports");

                            // securities can be set to either Bloomberg ticker or figi
                            //Element security = record.GetElement("security");
                            //string ticker = security.GetElementAsString("ticker");
                            //string figi = security.GetElementAsString("figi");

                            double sold = record.GetElementAsFloat64("sold");
                            double total = record.GetElementAsFloat64("total");
                            double traded = record.GetElementAsFloat64("traded");

                            System.Console.WriteLine("Broker: " + broker);
                            //System.Console.WriteLine("Rank: " + rank);
                            //System.Console.WriteLine("Ticker: " + ticker);
                            //System.Console.WriteLine("Figi: " + figi);
                            System.Console.WriteLine("Bought: " + bought.ToString() + "\tCrossed: " + crossed.ToString() + "\tHigh Touch: " + highTouch.ToString() + "\tLow Touch: " + lowTouch.ToString() +  
                                "\nNumber of Reports: " + numReports.ToString() + "\tSold: " + sold.ToString() + "\tTotal: " + total.ToString() + "\tTraded: " + traded.ToString());
                        }                                  
                    }

                    quit = true;
                    session.Stop();
                }
            }
        }

        private void processMiscEvents(Event evt, Session session)
        {
            System.Console.WriteLine("Processing: " + evt.Type);

            foreach (Message msg in evt)
            {
                System.Console.WriteLine("MESSAGE: " + msg);
            }
        }
    }
}

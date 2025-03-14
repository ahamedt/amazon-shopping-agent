# amazon-shopping-agent

Approach: 

The approach I took to tackle this problem was through the following steps:
- Build out the Amazon Web Tool
- Build out the Agent
- Integrate Both


1. Building out the Amazon Web Tool

To interact with the Amazon interface, I decided to use 
Selenium. I broke down the functionality to implement 
accoriding to the workflow below:

- navigate to Amazon
- search for the user's product in the search bar
- collect all of the links from the search page
- visit each link, and from each product page collect:
    - product name
    - price
    - description
    - rating out of 5
    - reviews
    - is available on prime


For extracting information from the web page, I decided to implement functions
that would test out a variety of selectors and try to get a valid value back from
the HTML of the product page. During testing, there would be instances where a selector I was originally using was no longer valid on the page. Therefore, to prevent this 
from being an issue, I decided to test out a variety of selectors to exhaustively
try to extract the relevant information from the HTML of the product page.

For avoiding bot detection and adding stealth to the web tool, I utilized the following:

- Using undetected_chromedriver in lieu of the standard Chrome driver used by Selenium
- Adding in random movements during the scraper's navigation, mimicking human behavior
- Adding in random user agents


For filtering, I implemented a filter function that is takes the user's search preferences and filters the products that have been collected from the search. 


Pros:
    - Simple, out of the box tool for interacting with web interfaces like Amazon
    - Widespread ecosystem + large amount of libraries
    - Multiple Browser Support
    - (For purposes of this project’s time constraints) faster time to implement due to past familiarity
Cons:
    - Large amount of boilerplate
    - Slow execution


Alternatives considered / tested out:

For interacting with Amazon:

- Using Playwright instead of Selenium
    - While Playwright would be a more performant / modern way of interacting with Amazon, for getting a 
    v0 ready as quickly as possible I decided to use selenium

- Initially getting the information for one product by visiting's product page and then going back to the search result page
to extract the next result's information
    - This caused Selenium to complain about stale elements on the web page, which I attributed to the fact that we were revisiting
    the search results page after going to a product page. 
    - The only way to get reviews and description for each product would be to visit each product's page, so we might as well
    collect them in an array and visit those links one by one, and extract all the relevant product information from the page

For stealthiness:

- selenium_stealth: Could not get this to work as it would always error out on my machine; Also outdated compared to undetected_webdriver

- Rate Limiting: For v0 workflow, rate limiting was not really an issue, but this would be an immediate follow up since it would be a very 
powerful tool to avoid detection / not overload the OpenAI api





2. Building the Agent

I decided to build the Agent as a single class that would process queries submitted by the user. In particular, I use GPT-4o as the model, and for every query that the user submits, the context of the full conversation that has been had so far is also provided to the endpoint call. 

The system prompt contains the bulk of the logic of how the Agent operates. It first provides the Agent with the context of the tool it has access to ("search_amazon"), as well as logic it should think about when it recieves a new user query:

    - if the user never searched for anything before or if the query is out of scope of the latest search results, then the Agent would decide to use the "search_amazon" tool to execute a new search, and then rank the search results in order of how well the results match the user's query.

    - if the user query is about the latest search results (follow up / refinement), then
    it should not execute a new search and just attempt to respond to the user query


Pros:
    - Simple agent for v0 (single class)
    - More fine grained control on how much autonomy is given to the Agent
    - Context Management is controlled programmatically
Cons:
    - More code to manage in long run
    - Orchestration, Handoff logic would need to be implemented manually
    - Need to manage context manage manually


Alternatives Considered
- Using OpenAI's Agents SDK / any other framework:

    - The Agent's SDK, while powerful and made it easy to make agents, was very new
    and seemed a bit better suited for multi agent workflows. Furthermore, it abstracted
    a lot of the finer grained functionality away (e.g. context management). 

    - Given that the scope of the v0 is relatively small, I had decided that creating an agent from scratch would achieve the same functionality while keeping the code
    to a manageable size without sacrificing control over what the Agent is doing 
    or how we manage the conversation / context being provided

- Making the Agent less Autonomous / more programmatic :

    - The Agent has several responsibilities:
        - determining if the user's query is follow up / refinement about the latest search
        - a query that requires a new search to be executed

    - Originally, I had a separate function that would attempt to classify the query
    first before programmatically deciding to call the search_amazon tool or not. However, I decided that was effectively taking Autonomy away from the agent to make it's own judgement about what to do, and so I decided to include in the system prompt
    that it should decide what to do based on the conversation history and the 
    the user query.


3. Integrating the Agent with the web tool

Allowing the Agent to integrate with the Web tool was relatively simple. I 
decided that on the Agent's initialization, it should have access to a ScraperManager
object that would manager the usage of the Amazon Scraper. I registered the call to 
search on amazon as a tool and provided it to the calls made to OpenAI.

Whenever a tool call would be made for "search_amazon", my process_query function
within my agent would call that tool, which in turn submits the search preferences
to the AmazonScraper to conduct a search on Amazon.

Since interacting with and searching on Amazon was a very clear external service, 
I decided that the Agent should interact with it as if it were a tool.



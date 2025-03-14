# Amazon Shopping Agent

## Approach

The approach I took to tackle this problem was through the following steps:
1. Build out the Amazon Web Tool
2. Build out the Agent
3. Integrate Both

### 1. Building out the Amazon Web Tool

To interact with the Amazon interface, I decided to use Selenium. I broke down the functionality to implement according to the workflow below:

- Navigate to Amazon
- Search for the user's product in the search bar
- Collect all of the links from the search page
- Visit each link, and from each product page collect:
  - Product name
  - Price
  - Description
  - Rating out of 5
  - Reviews
  - Prime eligibility

For extracting information from the web page, I implemented functions that test various selectors to get valid values from the HTML of product pages. During testing, I found that selectors would sometimes become invalid, so I implemented multiple selector options to ensure robust data extraction.

#### Avoiding Bot Detection

For avoiding bot detection and adding stealth to the web tool, I utilized:

- **Undetected ChromeDriver** instead of the standard Chrome driver
- Random movements during navigation to mimic human behavior
- Randomized user agents

For filtering, I implemented a function that takes the user's search preferences and filters the collected products accordingly.

#### Pros & Cons

**Pros:**
- Simple, out-of-the-box tool for interacting with web interfaces like Amazon
- Widespread ecosystem with many libraries
- Multiple browser support
- Faster implementation due to past familiarity (important for project time constraints)

**Cons:**
- Requires significant boilerplate code
- Slower execution

#### Alternatives Considered

**For interacting with Amazon:**

- **Playwright instead of Selenium**
  - While Playwright would be more performant and modern, I chose Selenium to get a v0 ready quickly

- **Sequential product information extraction**
  - Initially tried visiting a product page and then returning to search results
  - This caused Selenium to complain about stale elements
  - Decided to collect all product links first, then visit each one to extract information

**For stealthiness:**

- **selenium_stealth**: Could not get this to work as it would error out on my machine; also outdated compared to undetected_webdriver

- **Rate Limiting**: Not critical for v0, but would be an immediate follow-up to avoid detection and prevent OpenAI API overload

### 2. Building the Agent

I built the Agent as a single class that processes user queries. I used GPT-4o as the model, providing the full conversation context with each query.

The system prompt contains the core logic of how the Agent operates, providing context about the available "search_amazon" tool and decision-making guidelines:

- If the user never searched before or the query is outside the scope of latest results, use the "search_amazon" tool to execute a new search and rank results
- If the query is about latest search results (follow-up/refinement), respond without executing a new search

#### Pros & Cons

**Pros:**
- Simple agent implementation for v0 (single class)
- Fine-grained control over agent autonomy
- Programmatically controlled context management

**Cons:**
- More code to manage long-term
- Manual implementation of orchestration and handoff logic
- Manual context management

#### Alternatives Considered

- **OpenAI's Agents SDK or other frameworks:**
  - While powerful, the Agent SDK was very new and better suited for multi-agent workflows
  - It abstracted away fine-grained functionality like context management
  - Given the small scope of v0, creating an agent from scratch provided better control while keeping code manageable

- **Less autonomous/more programmatic approach:**
  - Considered having a separate function to classify queries before deciding to call the search tool
  - Decided this would reduce agent autonomy, so instead included decision-making logic in the system prompt

### 3. Integrating the Agent with the Web Tool

Integration was straightforward. The Agent is initialized with a ScraperManager object that manages the Amazon Scraper. I registered the Amazon search functionality as a tool and provided it to OpenAI.

When a "search_amazon" tool call is made, the process_query function submits search preferences to the AmazonScraper to conduct the search.

Since interacting with Amazon is clearly an external service, I designed the Agent to interact with it as a tool.

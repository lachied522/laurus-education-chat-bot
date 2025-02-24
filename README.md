# Customer Service Agent for Laurus Education

This Customer Service Agent was developed for Laurus Education. Below are instructions for setting up and deploying the agent.

## Prerequisites

1. A Meta developer account — If you don’t have one, you can [create a Meta developer account here](https://developers.facebook.com/).
2. A business app — If you don't have one, you can [learn to create a business app here](https://developers.facebook.com/docs/development/create-an-app/). If you don't see an option to create a business app, select **Other** > **Next** > **Business**.




## Step 3. Creating Google Custom Search Engine

Since Laurus Education has many partner colleges with their own domains, we will use a Google Custom Search Engine to act as the agent's knowledge base.

This means that the knowledge base will automatically be updated whenever changes are made to any of the websites.

1. Create a Google Developer Account
2. Visit the [Programmable Search Engine Console](https://programmablesearchengine.google.com/controlpanel/all) and add a new search engine
3. Select "Search specific sites or pages" and enter the following domains:
    - lauruseducation.com.au
    - allied.edu.au
    - hilton.edu.au
    - collinsacademy.edu.au
    - paragon.edu.au
    - ecoc.edu.au
    - everthought.edu.au
    - future.edu.au
4. Copy the search engine ID and store under GOOGLE_CSE_ID environment variable
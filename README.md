# Customer Service Agent for Laurus Education

This Customer Service Agent was developed for Laurus Education. Below are instructions for setting up and deploying the agent.

## Prerequisites

1. A Meta developer account — If you don’t have one, you can [create a Meta developer account here](https://developers.facebook.com/).
2. A Meta Business app — If you don't have one, you can [learn to create a business app here](https://developers.facebook.com/docs/development/create-an-app/). If you don't see an option to create a business app, select **Other** > **Next** > **Business**.

## Step 0: Creating OpenAI Developer Account


## Step 1: Create OpenAI Assistant

## Step 2: Create Whatsapp App


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

## Step 5. Deploy to AWS

## Step 6. Configuring Whatsapp callback URL for receiving messages

The final step is to provide Whatsapp with the callback url to forward messages to.

1. In the Meta App Dashboard, go to WhatsApp > Configuration.
2. Enter the Callback URL, paste the application url followed by /webhook
3. Enter a verification token. This string is set up by you when you create your webhook endpoint. You can pick any string you like. Make sure to update this in your WHATSAPP_VERIFY_TOKEN environment variable.

## Step 7. Increase API Gateway Maximum Integration Timeout

The default timeout for an integration between API Gateway and a Lambda is 29 seconds, which is too short for this use case. You will have to submit a request to AWS Service Quotas to increase the maximum timeout for the connection between API Gateway and Lambda.

1. In the AWS Console go to the Service Quotas Service
2. Inside Service Quotas, search API Gateway and click "View Quotas"
3. Search for the "Maximum integration timeout in milliseconds" quota
4. Click "Request an increase at account level" and set the value to 120,000 miliseconds (2 minutes)
5. Go back to API Gateway and click on Integration Request under the /{proxy+} endpoint
6. Click Edit and increase the timeout to 120,000 miliseconds
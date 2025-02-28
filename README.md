# Customer Service Agent for Laurus Education

This Customer Service Agent was developed for Laurus Education. Below are instructions for setting up and deploying the agent.

## Prerequisites

1. An OpenAI developer account - 
2. A Meta developer account — If you don’t have one, you can [create a Meta developer account here](https://developers.facebook.com/).
3. A Meta Business app — If you don't have one, you can [learn to create a business app here](https://developers.facebook.com/docs/development/create-an-app/). If you don't see an option to create a business app, select **Other** > **Next** > **Business**.
4. AWS account and the AWS CLI installed - follow steps at [here](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/prerequisites.html#prerequisites-configure-credentials)

## Step 0: Get OpenAI API key

We will require an OpenAI API key.

1. Go to https://platform.openai.com/api-keys and create a new secret key
2. Copy and paste the value into template.yaml under OPENAI_API_KEY

## Step 1: Create OpenAI Assistant

Run the following command to create the OpenAI assistant that will handle chat functionality. This will print the ID of the created assistant to the console.

```
python .\scripts\assistant.py
```

Copy and paste the assistant ID into template.yaml under OPENAI_ASSISTANT_ID.

## Step 2. Creating Google Custom Search Engine

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

## Step 3. Create Whatsapp App
Whatsapp provides two types of access tokens, a 24-hour one for development and a long-lasting one for production.

Firstly, go to **App settings** > **Basic** and copy and paste the App ID and App secret into template.yaml under WHATSAPP_APP_ID and WHATSAPP_APP_SECRET respectively.

Secondly, create a long-lasting access token for production:

1. Create a system user at the [Meta Business account level](https://business.facebook.com/settings/system-users)
2. On the System Users page, configure the assets for your System User, assigning your WhatsApp app with full control. Don't forget to click the Save Changes button
3. Click Generate new token and select the app, and then choose how long the access token will be valid. Choose the never expire option.
4. Select all the permissions (including non-Whatsapp permissions)
5. Copy and paste the access token into template.yaml under WHATSAPP_ACCESS_TOKEN

Finally, go back to **App Dashboard** >> **Whatsapp** >> **API Setup**. Here you will see a test number that can be used for development. If you wish to test the application copy and paste "Phone number ID" into template.yaml under PHONE_NUMBER_ID. Otherwise, follow the steps to create a Whatsapp business phone number.

Your environment in template.yaml should now look like this:

```yaml
WHATSAPP_ACCESS_TOKEN: *******************************************************************************
WHATSAPP_API_VERSION: v18.0
WHATSAPP_APP_ID: 1234567890
WHATSAPP_APP_SECRET: **************************
PHONE_NUMBER_ID: ************** # your business phone number id will go here once you create it
```

## Step 4. Deploy to AWS

We will use the AWS CLI to quickly and programmatically deploy the application.

Follow the steps at https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html to download the SAM CLI.

Once SAM CLI is configued, run the following command to deploy the application to AWS. Once the application has been deployed, ApiGatewayWebhookURL will be printed to the console. This is the callback url to give to Whatsapp in the next step.

```
sam deploy --guided
```

## Step 5. Configuring Whatsapp callback URL for receiving messages

The final step is to provide Whatsapp with the callback url to forward messages to.

1. In the Meta App Dashboard, go to WhatsApp > Configuration.
2. Enter the Callback URL, paste the application url followed by /webhook
3. Enter a verification token. This string is set up by you when you create your webhook endpoint. You can pick any string you like. Make sure to update this in your WHATSAPP_VERIFY_TOKEN environment variable.

## Step 6. Increase API Gateway Maximum Integration Timeout

The default timeout for an integration between API Gateway and a Lambda in AWS is 29 seconds, which is too short for this use case. You will have to submit a request to AWS Service Quotas to increase the maximum timeout for the connection between API Gateway and Lambda.

1. In the AWS Console go to the Service Quotas Service
2. Inside Service Quotas, search API Gateway and click "View Quotas"
3. Search for the "Maximum integration timeout in milliseconds" quota
4. Click "Request an increase at account level" and set the value to 120,000 miliseconds (2 minutes)
5. Go back to API Gateway and click on Integration Request under the /{proxy+} endpoint
6. Click Edit and increase the timeout to 120,000 miliseconds
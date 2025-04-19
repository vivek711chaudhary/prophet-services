# Prophet Service GCP Deployment Guide

This guide provides step-by-step instructions for deploying the Prophet Forecasting Service to Google Cloud Platform (GCP) using Cloud Run.

## Prerequisites

1. Google Cloud Platform account
2. Google Cloud SDK installed locally
3. Docker installed locally
4. Access to the MongoDB Atlas cluster

## Deployment Options

### Option 1: Manual Deployment with Cloud Run (Recommended)

1. **Login to Google Cloud:**
   ```bash
   gcloud auth login
   ```

2. **Set your GCP project:**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Build and Push the Docker Image:**
   ```bash
   # Navigate to prophet-service directory
   cd prophet-service
   
   # Build the image
   docker build -t gcr.io/YOUR_PROJECT_ID/prophet-service:latest .
   
   # Configure Docker to use gcloud as a credential helper
   gcloud auth configure-docker
   
   # Push the image to Google Container Registry
   docker push gcr.io/YOUR_PROJECT_ID/prophet-service:latest
   ```

4. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy prophet-service \
     --image gcr.io/YOUR_PROJECT_ID/prophet-service:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 2Gi \
     --set-env-vars="MONGODB_URI=mongodb+srv://vivekchaudhary52637:23mRD7YosUzFEXtt@engagements.magosmu.mongodb.net/,MODEL_CACHE_DIR=cache,DEBUG=False"
   ```

5. **Verify the Deployment:**
   - After deployment, Cloud Run will provide a service URL
   - Test the endpoint by visiting `https://prophet-service-HASH.run.app/`
   - You should see the message: "Prophet Forecasting Service is running"

### Option 2: Deployment with App Engine Flex

1. **Login to Google Cloud:**
   ```bash
   gcloud auth login
   ```

2. **Deploy to App Engine:**
   ```bash
   # Navigate to prophet-service directory
   cd prophet-service
   
   # Deploy to App Engine
   gcloud app deploy app.yaml
   ```

3. **Verify the Deployment:**
   - Access your app at `https://prophet-service-dot-YOUR_PROJECT_ID.appspot.com`

### Option 3: Automated Deployment with Cloud Build

1. **Connect your GitHub repository to Cloud Build**

2. **Create a build trigger:**
   - Go to Cloud Build > Triggers
   - Create a new trigger
   - Connect it to your GitHub repository
   - Set the build configuration to use the `cloudbuild.yaml` file

3. **When you push changes, Cloud Build will automatically:**
   - Build the Docker image
   - Push it to Container Registry
   - Deploy to Cloud Run

## Updating the Playwright MCP Application

After deployment, you'll need to update the Playwright MCP application to point to the new Prophet service endpoint:

1. **Update the API calls in `topicRoutes.js`**:
   
   Change lines like:
   ```javascript
   await axios.post('http://localhost:8000/api/v1/store-engagement', {...})
   ```
   
   To use the deployed endpoint:
   ```javascript
   await axios.post('https://prophet-service-HASH.run.app/api/v1/store-engagement', {...})
   ```

## Environment Variables

Remember to set the following environment variables in your Cloud Run deployment or app.yaml:

- `MONGODB_URI`: Your MongoDB connection string
- `MODEL_CACHE_DIR`: Directory for caching Prophet models
- `DEBUG`: Set to "False" in production

## Security Considerations

- The current deployment exposes the API publicly. For a production environment, consider:
  - Adding authentication to the API
  - Securing the MongoDB connection
  - Using Secret Manager for sensitive values
  - Setting up a VPC connector for private communication 
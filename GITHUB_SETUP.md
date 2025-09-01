# GitHub Setup Guide for VacationDesktop

## Step 1: Create a New Repository on GitHub

1. **Go to GitHub**:
   - Open your web browser
   - Go to [github.com](https://github.com)
   - Sign in with your existing account

2. **Create New Repository**:
   - Look for a green "New" button (usually in the top-left area)
   - OR click the "+" icon in the top-right corner and select "New repository"

3. **Repository Settings**:
   - **Repository name**: `vacationdesktop` (all lowercase, no spaces)
   - **Description**: `Multi-tenant travel advisor business platform`
   - **Visibility**: Choose "Public" (so Railway can access it easily)
   - **DO NOT** check "Add a README file" (we already have files)
   - **DO NOT** add .gitignore or license (we already have these)
   - Click the green "Create repository" button

4. **Copy the Repository URL**:
   - After creating, you'll see a page with setup instructions
   - Look for the URL that looks like: `https://github.com/yourusername/vacationdesktop.git`
   - Copy this URL (we'll need it in the next step)

## Step 2: Connect Your Local Project to GitHub

Now we'll upload your VacationDesktop code to GitHub.

1. **Open Terminal/Command Prompt**:
   - On Mac: Open Terminal
   - On Windows: Open Command Prompt or PowerShell
   - Navigate to your VacationDesktop folder:
   ```bash
   cd /Users/robertkemp/dev/VacationDesktop
   ```

2. **Connect to GitHub**:
   Replace `yourusername` with your actual GitHub username:
   ```bash
   git remote add origin https://github.com/yourusername/vacationdesktop.git
   ```

3. **Upload Your Code**:
   ```bash
   git push -u origin main
   ```

4. **GitHub Authentication**:
   - GitHub will ask for your username and password
   - **Important**: For password, you need a "Personal Access Token" (not your regular password)
   
   **If you don't have a token yet**:
   - Go to GitHub.com → Your profile picture → Settings
   - Scroll down to "Developer settings" → "Personal access tokens" → "Tokens (classic)"
   - Click "Generate new token (classic)"
   - Give it a name like "VacationDesktop Deploy"
   - Check these permissions:
     - ✅ repo (full control of private repositories)
     - ✅ workflow (if you plan to use GitHub Actions later)
   - Click "Generate token"
   - **COPY THE TOKEN IMMEDIATELY** (you won't see it again)
   - Use this token as your password when pushing

5. **Verify Upload**:
   - Go back to your GitHub repository page
   - Refresh the page
   - You should see all your VacationDesktop files!

## Step 3: Deploy to Railway

Now that your code is on GitHub, let's deploy it!

1. **Go to Railway**:
   - Open [railway.app](https://railway.app) in your browser
   - Click "Login" or "Start a New Project"
   - **Sign up with GitHub** (this makes connecting easier)

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - You should see your `vacationdesktop` repository
   - Click on it

3. **Wait for Deployment**:
   - Railway will automatically start building your app
   - You'll see logs showing:
     - Installing Python dependencies
     - Running database migrations
     - Collecting static files
   - This takes about 3-5 minutes

4. **Add Database**:
   - In your Railway project dashboard
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway will automatically create the database and set DATABASE_URL

5. **Configure Environment Variables**:
   Click on your web service, then go to "Variables" tab and add:

   ```
   SECRET_KEY = django-insecure-your-new-secret-key-here-make-it-long-and-random
   DEBUG = False
   EMAIL_HOST_PASSWORD = G0lfer99%7458720
   ```

   **Generate a new SECRET_KEY**:
   - Go to [djecrety.ir](https://djecrety.ir/)
   - Copy the generated key
   - Paste it as your SECRET_KEY value

6. **Get Your App URL**:
   - In Railway dashboard, you'll see a "Deployments" section
   - Click on the latest deployment
   - You'll see a URL like: `https://vacationdesktop-production-1234.up.railway.app`
   - This is your live app!

## Step 4: Create Your Admin User

1. **Open Railway Console**:
   - In your Railway project
   - Click on your web service
   - Look for "Deploy Logs" or "Console" tab
   - Or use the Railway CLI if you have it

2. **Create Superuser**:
   In the Railway console, run:
   ```bash
   python manage.py createsuperuser
   ```
   - Enter a username (like `admin`)
   - Enter your email
   - Create a secure password
   - Remember these credentials!

## Step 5: Test Your Live App

1. **Visit Your App**:
   - Go to your Railway URL
   - You should see the VacationDesktop login page!

2. **Login**:
   - Use the superuser credentials you just created
   - You should see the dashboard

3. **Test Features**:
   - Create a tenant (client organization)
   - Add a client user
   - Create a support ticket
   - Check that email notifications work

## Troubleshooting

### "Permission denied" when pushing to GitHub:
- Make sure you're using your Personal Access Token, not your password
- Check that the repository URL is correct

### Railway deployment fails:
- Check the build logs in Railway dashboard
- Make sure all environment variables are set
- Verify your requirements.txt is complete

### App shows 500 error:
- Check Railway deployment logs
- Verify DATABASE_URL is automatically set
- Make sure SECRET_KEY is set and DEBUG=False

### Email notifications don't work:
- Verify EMAIL_HOST_PASSWORD is set correctly in Railway
- Check that the Mailgun credentials are still valid

## 🎉 Success!

Once everything is working, you'll have:
- ✅ Your code safely stored on GitHub
- ✅ A live app running on Railway
- ✅ Professional URL to share with colleagues
- ✅ Automatic deployments (when you push code changes)

**Your live URL will be something like**:
`https://vacationdesktop-production-1234.up.railway.app`

Share this URL with your colleagues to show off the VacationDesktop platform!
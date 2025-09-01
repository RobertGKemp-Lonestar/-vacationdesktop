# VacationDesktop Deployment Guide

## 🚀 Quick Deployment to Railway (Recommended)

Railway is the easiest option for deploying VacationDesktop for demos.

### Prerequisites
- GitHub account
- Railway account (free tier available)

### Step 1: Push to GitHub

1. Create a new repository on GitHub called `vacationdesktop`
2. Push your code:
   ```bash
   git remote add origin https://github.com/yourusername/vacationdesktop.git
   git push -u origin main
   ```

### Step 2: Deploy to Railway

1. Go to [railway.app](https://railway.app)
2. Sign up/Login with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your `vacationdesktop` repository
6. Railway will automatically:
   - Detect it's a Django app
   - Install dependencies from requirements.txt
   - Create a PostgreSQL database
   - Set DATABASE_URL automatically

### Step 3: Configure Environment Variables

In Railway dashboard, add these environment variables:

**Required:**
- `SECRET_KEY` = `generate-a-new-secure-secret-key-here`
- `DEBUG` = `False`
- `ALLOWED_HOSTS` = `yourdomain.railway.app`

**Email (Mailgun):**
- `EMAIL_HOST_PASSWORD` = `your-mailgun-password`

**Optional Security:**
- `SECURE_SSL_REDIRECT` = `True`
- `SESSION_COOKIE_SECURE` = `True` 
- `CSRF_COOKIE_SECURE` = `True`

### Step 4: Create Superuser Account

In Railway web terminal or CLI:
```bash
python manage.py createsuperuser
```

### Step 5: Access Your App

Your app will be available at: `https://yourdomain.railway.app`

## 🌐 Alternative: Render Deployment

1. Push to GitHub (same as above)
2. Go to [render.com](https://render.com)
3. Create new Web Service from GitHub repo
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python manage.py migrate && python manage.py collectstatic --noinput && gunicorn vacationdesktop.wsgi`
5. Add PostgreSQL database
6. Set same environment variables as Railway

## 📧 Email Configuration

The app is pre-configured for Mailgun SMTP. Update these in production:

- Domain: `kemp-it.com` (or your domain)
- From Email: `forms@kemp-it.com` (or your email)
- SMTP Password: Use your production Mailgun password

## 🔐 Security Checklist

Before going live:
- [ ] Generate new SECRET_KEY for production
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS with your domain
- [ ] Enable HTTPS redirects
- [ ] Secure cookie settings
- [ ] Change default admin password
- [ ] Review email credentials

## 🎯 Features Ready for Demo

Your deployed VacationDesktop includes:

✅ **Multi-tenant Architecture**
- Separate tenants for different travel agencies
- Role-based access control (RBAC)

✅ **Support System**
- Ticket creation and management
- Email notifications to clients
- Staff dashboard for helpdesk users

✅ **User Management**
- Staff can create client users
- Profile management
- Password reset functionality

✅ **Professional UI**
- Clean Bootstrap interface
- Responsive design
- Mobile-friendly

## 🧪 Testing Your Deployment

1. **Login**: Use your superuser account
2. **Create Tenant**: Add a client organization
3. **Create Client User**: Add user for that tenant
4. **Create Ticket**: Test the support system
5. **Email Test**: Verify notifications work

## 💰 Pricing

**Railway**: Free tier includes 500 hours/month, $5/month for unlimited
**Render**: Free tier for static/web apps, $7/month for databases

Perfect for demos and client presentations!

## 🆘 Need Help?

Common issues:
- **500 Error**: Check environment variables are set
- **Database Error**: Ensure PostgreSQL is connected
- **Static Files**: Run `collectstatic` command
- **Email Issues**: Verify Mailgun credentials

Your VacationDesktop is now ready to show to colleagues! 🎉
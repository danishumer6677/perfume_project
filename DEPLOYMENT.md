# Deploying Django Perfume Project to Vercel

## Prerequisites
1. **Database**: Since Vercel doesn't support SQLite in production, you'll need a PostgreSQL database. Recommended options:
   - [Neon](https://neon.tech/) (Free tier available)
   - [Supabase](https://supabase.com/) (Free tier available)
   - [Railway](https://railway.app/) (Free tier available)

## Environment Variables
Set these in your Vercel dashboard:

\`\`\`
SECRET_KEY=your-django-secret-key
DEBUG=False
DATABASE_URL=postgresql://username:password@host:port/database_name
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
CONTACT_EMAIL=your-email@gmail.com
\`\`\`

## Deployment Steps

1. **Push to GitHub**: Make sure your code is in a GitHub repository

2. **Connect to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Vercel will automatically detect it's a Python project

3. **Configure Build Settings**:
   - Build Command: `bash build.sh`
   - Output Directory: Leave empty
   - Install Command: `pip install -r requirements.txt`

4. **Set Environment Variables**: Add all the environment variables listed above

5. **Deploy**: Click deploy and wait for the build to complete

## Important Notes

- **Database Migration**: The first deployment will run migrations automatically
- **Static Files**: Handled by WhiteNoise middleware
- **Media Files**: For production, consider using cloud storage (AWS S3, Cloudinary)
- **Email**: Configure SMTP settings for production email functionality

## Troubleshooting

- If deployment fails, check the build logs in Vercel dashboard
- Ensure all environment variables are set correctly
- Database connection issues are the most common problem

## Local Development vs Production

- Local: Uses SQLite database
- Production: Uses PostgreSQL (via DATABASE_URL)
- Static files are handled differently in each environment

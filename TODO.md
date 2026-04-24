# Azure Deployment Fix TODO

## Completed Fixes
1. [x] Delete duplicate nested `student_dashboard/` folder
2. [x] Fix `.gitignore` merge conflict markers
3. [x] Delete old conflicting `.github/workflows/deploy.yml`
4. [x] Create `startup.sh` (Linux bash startup script)
5. [x] Delete `startup.ps1` (Windows-only, won't run on Azure Linux)
6. [x] Update `.deployment` to point to `startup.sh`
7. [x] Remove heavy ML deps from `requirements.txt`, create `requirements-dev.txt`
8. [x] Add graceful fallback in `dashboard/recommendation.py`
9. [x] Simplify `web.config`
10. [x] Verify `run_waitress.py` binds `0.0.0.0:$PORT`
11. [x] Commit and push to GitHub

## Next Steps for User (Deploy via VS Code Azure Extension)
1. **Set Azure App Service environment variables** in Azure Portal:
   - Go to your App Service → Configuration → Application settings
   - Add `SECRET_KEY` = generate one with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
   - Add `DEBUG` = `False`
   - Ensure `SCM_DO_BUILD_DURING_DEPLOYMENT` = `true` (should already be set)

2. **Deploy from VS Code**:
   - Open Command Palette (`Ctrl+Shift+P`)
   - Type: `Azure App Service: Deploy to Web App`
   - Select your subscription and the `studentdashboard` app
   - Select the `f:/sem7/sc_pbl/student_dashboard` folder
   - Confirm deployment

3. **Check logs**:
   - Azure Portal → your App Service → Monitoring → Log stream
   - Look for `=== Starting Dashboard Application ===`

4. **If recommender needs full ML features locally**:
   - Run: `pip install -r requirements.txt -r requirements-dev.txt`


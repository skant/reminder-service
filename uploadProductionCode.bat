@echo OFF
echo 		----------------------------------------
echo 		You are about to upload PRODUCTION code
echo 		Press any continue OR close this window
echo 		----------------------------------------
pause > nul


ren config.cfg        config_dev.cfg
ren config_prod.cfg   config.cfg

ren app.yaml         app_dev.yaml
ren app_prod.yaml    app.yaml
@echo ON

appcfg.py --no_cookies update .

@echo OFF
ren config.cfg       config_prod.cfg
ren config_dev.cfg   config.cfg

ren app.yaml         app_prod.yaml
ren app_dev.yaml     app.yaml
@echo ON


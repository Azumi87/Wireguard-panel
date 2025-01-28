![R (2)](https://github.com/Azumi67/PrivateIP-Tunnel/assets/119934376/a064577c-9302-4f43-b3bf-3d4f84245a6f)
نام پروژه :  داشبورد وایرگارد با ربات (فارسی و انگلیسی)
---------------------------------------------------------------
----------------------------------

**این پروژه از xray استفاده نمیکند و تمام کارها را خود وایرگارد انحام میدهد.‌xray برای وارپ اضافه شده بود اما چون از خود وایرگارد استفاده میکنیم، از وارپ و xray نمیشود استفاده کرد.تنها وارپی که میتونم اصافه کنم وارپ wgcf و پلاس ان میباشد.**

**قسمت هایی از اموزش ها و نوشتارها پاک شده است چون از ان بک اپ نداشتم اما پروژه فکر کنم اپدیت باشد**

**همیشه قسمت اپدیت را مطالعه بفرمایید و نسبت به اپدیت پنل اقدام نمایید. از طریق لینک اسکریپت و گزینه 1**

**این پروژه اموزشی است و استفاده از ان بر عهده شما می‌باشد. در صورت وجود مشکل باعث ناراحتی شما نشود. نخست تست بفرمایید و در صورت نیاز از استفاده نمایید**

--------

 <div align="right">
  <details>
    <summary><strong><img src="https://github.com/user-attachments/assets/bf3c8113-cdd1-4c57-a744-796d7530d565" alt="Image"> مشکلات تایم زون مختلف (بخوانید)</strong></summary>

------------------------------------ 

- اگر اوپتیمایزر نصب کردید و محاسبه زمان و حجم توقف کرد، حتما به خاطر وجود دو تایم زون در سیستم شما است که تا برطرف نشود، مشکل شما هم حل نمیشود
- باید از دستورات زیر استفاده نمایید تا تایم زون و لوکال تایم با هم سینک باشند
- بعد از سینک کردن ان، باید پنل را ریست نمایید
 <div align="left">
  
```
cat /etc/timezone
به طور مثال این را میبینید : Etc/UTC, Europe/Berlin
ls -l /etc/localtime
به طور مثال این را میبینید :  /usr/share/zoneinfo/Europe/Berlin
خب بین انها تضاد آست و باید درست شود
echo "Europe/Berlin" | sudo tee /etc/timezone
sudo dpkg-reconfigure -f noninteractive tzdata
cat /etc/timezone
ls -l /etc/localtime
بررسی کنید هر دو یکی باشد
timedatectl
حالا اگر همه چی درست بود باید پنل را ریست نمایید
```

------------------------------------ 

  </details>
</div>
 <div align="right">
  <details>
    <summary><strong><img src="https://github.com/user-attachments/assets/0ddf06f0-04c1-4d5a-bbb8-d784015e93d2" alt="Image"> مشکلات احتمالی (بخوانید)</strong></summary>

------------------------------------ 

- اگر سرور شما مشکل dns دارد اول مشکل ان را رفع کنید یا از سرور و Os ای استفاده کنید که چنین مشکلی ندارد. حتی میتوانید dns را از قسمت کانفیگ وایرگارد پاک کنید
- ترجیجا از دبیان 12 استفاده نمایید. من بر روی دبیان 12 و amd مشکلی نداشتم
- دو کاربر با نام یکسان در یک اینترفیس نسازید.
- همیشه اگر مشکلی دارید لطفا فسمت لاگ ها را نگاه کنید یا گزینه debug در config.yaml را به true تغییر دهید
- اگر سرویس شما به هنگام ریست از کار می افتد مشکل شما در virtual env است . پوشه venv در /usr/local/bin/Wireguard-panel/src . ان مشکل را برطرف کنید
- اگر از os ای استفاده میکنید که مشکلات iproute و wireguard tools دارد لطفا اطمینان یابید که چنین مشکلاتی ندارد . در این پنل از مسیر اصلی دستورات که داخل sbin هستند استفاده شده است/چند نمونه مثال پایین اوردم. اگر این مورد خیلی اذیت کرد لطفا اطلاع دهید که مسیر اصلی را پاک کنم و این مشکل حل بشود اما نباید روی بیشتر os ها مشکلی داشته باشد
- فعلا مسیر اصلی دستورات را پاک کردم و این موضوع در bandit به عنوان مورد قابل بازبینی در نظر گرفته میشود تا ببینم بعدا چی میشه
- باید توجه داشته باشید که از داخل موبایل، من پنل را تست نکردم.ممکن است با مشکلاتی مواجه شوید یا با کامپیوتر به ان متصل شوید یا برای مویایل از طریق بات استفاده نمایید.
- کانفیگ وایرگارد را از wg0.conf آغاز کنید و نام های رندوم ندهید
- یوزر و پسورد خود را فراموش نکنید و از گزینه remember me استفاده نمایید
- لطفا حتما به سیستم عامل نصبی خود دقت کنید که چنین مشکلاتی نداشته باشد وگرنه پنل برای شما کار نخواهد کرد.
- اگر دیگران هم دوست داشتند میتوانند سایر os ها را تست کنند و به پنل اضافه کنند .
- پنل اختلالی در تانل شما به وجود نمی اورد. از لوکال ایپی ها همراه با تانل استفاده نمایید. حتما cache و data storage کلاینت خود را در موبایل پاک نمایید. ممکن تانل شما برای این مورد کار نکند.
- از ایپی لوکال در صورت محدودیت بر روی سرورتان استفاده نمایید. به طور مثال geneve - لینک اسکریپت لوکال : https://github.com/Azumi67/6TO4-GRE-IPIP-SIT
- بعد از اپدیت پنل همیشه پنل را ریست کنید. اپدیت هم که به این صورت میباشد که wire را میزنید و گزینه 10  یا از اسکریپت دانلود ، ان را داخل سرور اجرا میکنید و گزینه اول. بعد از اتمام اپدیت، لطفا پنل و بات را ریست نمایید
 <div align="left">
  
```
sudo apt update
sudo apt install iproute2
which ip
باید این مسیر /sbin/ip را نشان دهد
export PATH=$PATH:/sbin:/usr/sbin
sudo chmod +x /sbin/ip

و برای وایرگارد
sudo apt update
sudo apt install wireguard-tools
which wg-quick
sudo ln -s $(which wg-quick) /sbin/wg-quick
sudo chmod +x /sbin/wg-quick

which wg
باید به این صورت باشد
/usr/bin/wg

```

------------------------------------ 

  </details>
</div>

 <div align="right">
  <details>
    <summary><strong><img src="https://github.com/user-attachments/assets/0ddf06f0-04c1-4d5a-bbb8-d784015e93d2" alt="Image"> مشکلات DNS (بخوانید)</strong></summary>

------------------------------------ 

- سرور شما مشکل dns داشته باشد هم کارایی پنل پایین خواهد امد و هم بات از کار می افتد. من از داخل اسکریپت قسمت dns هم برداشتم
- اگر سرور شما مشکل dns دارد، میتوانید از اوپتیمایزر استفاده کنید
- بر روی سرور debian 12 و ubuntu24 میتوانید از دستورات زیر استفاده نمایید
<div align="left">
  
```
sudo nano /etc/systemd/resolved.conf

این مقادیر را به آن اضافه کنید
[Resolve]
DNS=1.1.1.1 8.8.8.8
FallbackDNS=1.0.0.1 8.8.4.4
### now Ctrl + x , y to save ###

sudo systemctl restart systemd-resolved
sudo rm /etc/resolv.conf
sudo ln -s /run/systemd/resolve/resolv.conf /etc/resolv.conf
حالا بررسی کنید که تغییرات اعمال شده است
cat /etc/resolv.conf

```
 <div align="right">
- اگر کانفیگ /etc/resolv.conf شما هر چند دقیقه ریست میشود هم میتوانید با کرون جاب اینکار را انجام دهید

 <div align="left">
  
```
crontab -e
اینو اضافه کنید
* * * * * echo -e "nameserver 1.1.1.1\nnameserver 1.0.0.1" > /etc/resolv.conf

ذخیره کنید و خارج شوید

```
 <div align="right">

- اگر مشکل شما حتی با اوپتیمایزر و پاک کردن dns وایرگارد و حتی systemd-resolve و ست کرون جاب هم درست نشد باید سرور خود را عوض کنید . ترجیحا از دبیان 12 amd استفاده نمایید
- من تا حالا روی سرور های دیجیتال اوشن که تست کردم مشکلی نداشتم.

------------------------------------ 

</details>
</div>

 <div align="right">
  <details>
    <summary><strong><img src="https://github.com/user-attachments/assets/79ca8970-1e05-4e60-bc7c-aa12f3573bbc" alt="Image"> ست کردن قالب دلخواه</strong></summary>

------------------------------------ 
- در قسمت Peers یک قالب دیفالت وجود دارد. میتوانید از قالب دلخواه خود استفاده نمایید
- یک قالب در ابعاد 430 در 500 درست کنید ور در قسمت usr/local/bin/Wireguard-panel/src/static/images با نام template.jpg قرار دهید
- پنل را ریست نمایید . از این به بعد قالب شما به نمایش در خواهد امد

------------------------------------ 

</details>
</div>

 <div align="right">
  <details>
    <summary><strong><img src="https://github.com/user-attachments/assets/dbbc44c0-06c0-405d-80f8-fb8c3a79a874" alt="Image"> نحوه گزارش و debug</strong></summary>

------------------------------------ 
- اگر مشکلی در خود پنل و اجرا نشدنش دارید با دستورهای زیر میتوانید مشکل را متوجه شوید
 <div align="left">
  
```
systemctl status wireguard-panel
systemctl stop wireguard-panel
---------------------------------------
## change debug=false >> debug=true

nano /usr/local/bin/Wireguard-panel/src/config.yaml
پس از تغییر دیباگ، ان را ذخیره کنید و خارج شوید
/usr/local/bin/Wireguard-panel/src/venv/bin/python3 /usr/local/bin/Wireguard-panel/src/app.py
حالا باید ببینید چه خطایی گرفتید تا بشود مشکل شما را فهمید
```
 <div align="right">
  
- برای سرویس های بات هم به همین صورت عمل میکنیم
 <div align="left">
  
```
بسته به نوع سرویس فارسی یا انگلیسی
systemctl status telegram-bot-fa
systemctl stop telegram-bot-fa
/usr/local/bin/Wireguard-panel/src/venv/bin/python /usr/local/bin/Wireguard-panel/src/telegram/robot-fa.py
برای انگلیسی
systemctl status telegram-bot-en
systemctl stop telegram-bot-en
/usr/local/bin/Wireguard-panel/src/venv/bin/python /usr/local/bin/Wireguard-panel/src/telegram/robot.py

حالا باید خطا را ببینید و مشکل را حل کنید
```
<div align="right">
 
- پس از رفع مشکل، سرویس ها را ریست نمایید

---------------

</details>
</div>


 <div align="right">
  <details>
    <summary><strong><img src="https://github.com/user-attachments/assets/1bd45cc6-b800-40b1-a94d-03ed1dac6ce5" alt="Image"> تانل</strong></summary>

------------------------------------ 
- من خودم از لوکال ایپی geneve با پورت فوروارد خودم استفاده میکنم (مصرف شخصی دارم) : https://github.com/Azumi67/proxyforwarder 
-  شما میتوانید از لوکال و dokodemo استفاده نمایید.
- ممکن است پورت فوروارد به کار شما نیاید. برای همین میتوانید از ریورس های frp یا backhaul و حتی تانل udp2raw و چیزل استفاده نمایید.
- برای لوکال ایپی هم میتوانید از این اسکریپت استفاده نمایید : https://github.com/Azumi67/6TO4-GRE-IPIP-SIT
- اگر باز هم مشکل داشتید باید چند کار انجام دهید . با نصب اوپتیمایزر هم تانل را تست کنید و حواستان به فایروال ufw هم باشد
- دقت کنید گاهی اوقات کلاینت وایرگارد در کامپیوتر و موبایل میتواند باعث stuck شدن 92B شود. کامپیوتر را ریست کنید و در داخل موبایل date storage و cache را خالی نمایید
- اگر باز هم مشکل داشتید باید سرور خارج خود را عوض کنید. سپس مشکل شما حل میشود
- بیشتر مورد های تانل وایرگارد در همین موارد خلاصه میشود



</details>
</div>
<div align="right">
  <details>
    <summary><strong><img src="https://github.com/user-attachments/assets/5ca10d06-15c9-45b6-99d0-498bf4e80c9c" alt="Image"> نحوه گرفتن بک اپ</strong></summary>

------------------------------------ 

- از داخل پنل یا بات یک backup دستی ایجاد نمایید. این در پوشه backups با نام manualbackup.zip ذخیره میشود.
- این فایل از محتویات wg interface و db بک اپ میگیرد .
- در صورت نصب پنل جدید همین فایل را در پوشه backups قرار دهید و توسط بات یا پنل ریستور کنید. گزینه ای با این نام داخل پنل و بات موجود میباشد
- روش دیگر برای بازگردانی بک اپ کاربران باز کردن این فایل zip و کپی کردن محتویات فایل های wg0.conf یا wg1.conf به داخل پوشه etc/wireguard است و پوشه db هم در داخل usr/local/bin/Wireguard-panel/src/db بریزید
- یا میتوانید از کل پنل یک کپی در روی کامپیوتر خود بریزید. بهتر است این روش ها را از قبل تست نمایید تا با نحوه کار آن اشنا شوید
- بعد از بازگردانی بک اپ، باید سرویس پنل(wireguard-panel) و بات را ریست نمایید و تمام اینترفیس ها هم باید یک بار غیر فعال و دوباره فعال بشوند.



</details>
</div>

-------------------

**سایر توضیحات:**

- این پنل توسط من کاملا تست شده است و کار میکند. اگر مشکلی در نصب آن داشتید با مطالعه نحوه ریپورت کردن، ان را در گیت هاب گزارش دهید.
- اگردرخواست رفع باگی یا اضافه کردن feature ای داشتید تنها در قسمت Issues بیان کنید تا در صورت توان، مشکل را حل و درخواستی را اضافه کنم.
- اطمینان حاصل کنید که قبل از نصب پنل، مشکل dns و تایم زون ندارید. سرور ریبیلد شده باشد. اگر مشکل dns داشته باشد ممکن است سرور شما در دریافت اطلاعات کند باشد و همچنین در بات هم مشکل‌دار خواهد شد. سیستم عامل خود را بررسی کنید.(مطالب را در بالا مطالعه بفرمایید)
- در این داشبورد از طریق خود پنل، امکان نصب بات تلگرام وجود دارد. باید دقت نمایید که نصب فارسی با نصب انگلیسی متفاوت میباشد و از قسمت مربوطه نصب نمایید
- در این پنل از json برای محدودیت حجم و مانیتورینگ استفاه شده است. 
- در این پنل امکان جابجایی فایل های پشتیبان از سروری به سرور دیگر امکان پذیر است تنها باید دقت کنید که نام اینترفیس وایرگارد را تغییر ندهید و اینترفیس اصلی eth یا ens در کانفیگ وایرگارد ذکر شود. به طور مثال اگر در سرور اول اینترفیس اصلی شما eth است در سرور دوم در صورت تغییر اینترفیس اصلی، ان را در wg0.conf ویرایش نمایید.
- پنل با تانل شما کاری ندارد و تنها management انجام میدهد
- در این پنل تلاش کردم در حد توان از sanitazation و استفاده از مسیر اصلی دستورات استفاده بشود تا جای ممکن از shell injection جلوگیری شود.
- در حال حاضر مسیر های اصلی دستورات برداشته شده است تا بعدا شاید دوباره اضافه کنم
- توجه داشته باشید دکمه فعال و غیر فعال کردن، حجم و زمان هم ریست میکند و در بات هم به همین صورت است
- بعدا بررسی sanitization قبل از subprocess تکمیل خواهد شد که خطاهای bandit هم کم شود
- بر روی ubuntu 24 & debian 12 تست شده است
- دقت نمایید برای اینکه پنل و feature های حجم و زمان به درستی کار کند باید سرویس wireguard-panel همیشه بدون مشکل کار کند. بهتر است گهگاهی این سرویس را بررسی کنید. البته در صورت نصب بات، در صورت قطع سرویس به شما notify میشود.


----------------------------------

![check](https://github.com/Azumi67/PrivateIP-Tunnel/assets/119934376/13de8d36-dcfe-498b-9d99-440049c0cf14)
**امکانات و نکات**

- مدیریت حجم به صورت MiB , GIB
- مدیریت زمان به صورت روز و ماه و ساعت و دقیقه
- نمایش available ips برای اساس ایپی پرایوت انتخابی شما ( تنها 30 تا را به صورت همزمان در پنل نشان میدهد)
- استفاده از Json فایل برای پشتیبانی و مدیریت و مانیتورینگ
- امکان پشتیبان گیری اتوماتیک و دستی و بازگردانی آن
- نمایش اینترفیس وایرگارد و کاربران
- نمایش cpu و disk و ram در صفحه اصلی
- پشتیبانی از زبان فارسی و انگلیسی تنها با یک بار نصب
- دارای اسکریپت نصب
- دارای ربات ادمین برای ساخت و ویرایش کاربر و پشتیبان گیری و سایر موارد به زبان انگلیسی و فارسی ( از داخل پنل نصب میشود)
- دارای وارپ پایه به صورت wgcf و xray (به صورت ازمایشی اضافه شده است)
- امکان تغییر دادن تنظیمات وایرگارد و flask از داخل پنل
- پشتیبانی از tls توسط certbot
- دارای نمایش قالب default برای کاربران و qr code و دانلود کانفیگ
- دارای ریست حجم و زمان و دکمه های فعال یا غیر فعال کردن
- دارای pagination به این صورت که هر 10 کاربر در یک صفحه قرار میگیرد
- دارای نمایش لاگ و ایپی های سرور و سرویس بات و وارپ و غیره
- دارای نمایش notification برنامه در ربات ادمین
- دارای محاسبه زمان پس از اتصال اول
- پشتیبانی بات از چندین admin chat id
- پشتیبانی endpoint از ساب دامین و ایپی
- مشاهده کانفیگ توسط کاربر با لینک کوتاه (به اسکرین شات برای مشاهده template مراجعه کنید)
-------
  <div align="right">
  <details>
    <summary><strong><img src="https://github.com/Azumi67/Rathole_reverseTunnel/assets/119934376/3cfd920d-30da-4085-8234-1eec16a67460" alt="Image"> آپدیت</strong></summary>
  
------------------------------------ 

- ربات فارسی و انگلیسی اپدیت شد که منو های compact mode داشته باشد
- اسکریپت اپدیت شد که با فراخوانی wire اجرا شود
- اپدیت app.py برای ریدایرکت صفحه register به لاگین در صورت وجود نام کاربری و گذرواژه ( thanks to opiran for mentioning that)
- اپدیت script-fa.js برای حل مشکل refresh peer list در هنگام فیلتر فعال.
- مشکل بالا نیامدن پنل با اضافه شدن pytz module حل شد
- فغلا مسیر اصلی دستورات را پاک کردم و این موضوع در bandit به عنوان مورد قابل بازبینی در نظر گرفته میشود تا ببینم بعدا چی میشه
- اپدیت اسکریپت : از این به بعد میتوانید توسط دستور اسکریپت چه با download.sh یا wire به اپدیت پنل بپردازید ( به صورت ازمایشی اضافه شده است)
- برای بات : تنها chat admin id دسترسی به بات را خواهد داشت
- برای بات : در قسمت peer creation ، اطلاعات کاربر ساخته شده کامل تر شد و mtu هم به ان اضافه شد
- برای بات : فسمت first usage همان محاسبه زمان پس از اتصال اول میباشد
- برای بات : در قسمت settings مشکل mtu برطرف شد
- اپدیت استفاده از چندین admin chat id اضافه شد. با کاما استفاده نمایید مانند 674565756, 6545675
- اپدیت استفاده از ساب دامین به جای Ip هم اضافه شد
- اپدیت encryption فایل telegram.yaml اضافه شد
- اپدیت برای disable & enable notifications که بر اساس health app.py کار کند
- اپدیت pagination انجام شد که دیگر به صفحه نخست باز نگردد
- بات فارسی مشکل پاک شدنش برطرف شد
- اپدیت keepalive به بات اضافه شد
- اپدیت available ips برای بات اضافه شد. از این به بعد به درستی باید ایپی های موجود را نشان دهد
- اپدیت تایم زون در app.py انجام شد
- مشکلات delete peer در صفحه اصلی حل شد
- اپدیت app.py برای مانیتور ترافیک که پس از ریبوت سرور، حجم های مصرفی ریست نشود
- مشکلات mismatch در json فایل برطرف شد
- مشکل ریست و ویرایش نکردن در برنامه برای اینترفیس های به غیر از دیفالت برطرف شد
- اپدیت برای بات : اضافه شدن اطلاعات اضافی برای دانلود کانفیگ و کد qr
- اپدیت برای اسکریپت که از این به بعد قالب های شما را overwrite نکند . از طریق اسکریپت داخل گیت هاب اپدیت نمایید( پس از اپدیت حتما پنل و بات را ریست نمایید)
- اپدیت بات : ریست حجم و ترافیک باید به درستی کار کند
- اپدیت بات : نمایش محتویات conf فایل در زیر آن
- فعلا به json فایل ها tmp قبل از ذخیره کردن اضافه کردم و برای مانیتور و decrement هم قفل گذاشتم تا ببینم مشکل پاک شدن json فایل حل میشود یا خیر
- اضافه شدن اپدیت برای نمایش ندادن کاربرهای اینترفیس در صورت استفاده از pagination
- اضافه کردن چک باکس فعال در صورت وجود geosites
- به تمام مسیر هایی که فایل json را رایت میکند قفل اضافه کرده ام تا نتیجه اش را ببینم. (ممکن است دستور شما تا اجرا شدنش زمان ببرد. دلیلش قفل میباشد که تا دستور قبلی کامل نشود بعدی اجرا نمیشود)
- اپدیت بلاک کردن کاربر زمانی که منقضی شود. الان باید به درستی بلاک کند.
- برای کاربرها template مشاهده کانفیگشان اضافه شد. در داخل بات پس از ساخت کانفیگ در قسمت دانلود کانفیگ یا qr به عنوان لینک کوتاه کانفیگ قابل مشاهده است. در دانلود کانفیگ و qr هم به صورت جداگانه نشان داده خواهد شد
- مشکلات short link و عدم نمایش ساعت در template برطرف شد
- مشکل محدودیت نمایش کاربر برطرف شد
- اپدیت برای template که به درستی زمان و حجم باقی مانده را نشان دهد
- اپدیت برای pagination انجام شد. انیمشن transition برای کانفیگ وایرگارد و pagination اضافه شد.
- اپدیت برای حذف کردن اضافه شد که اگر در ان صفحه کاربری موجود نبود به صفحه قبل بازگردد. اگر موجود بود در همان صفحه بماند. برای ویرایش کاربر هم به همین صورت میباشد
- اپدیت برای toggle peer اضافه شد که در صورت فعال کردن کاربر، به درستی ترافیک ریست شود یعنی نخست پابلیک کی پاک شود و سپس اضافه شود که در ریست ترافیک به تنهایی انجام میشد اما در toggle peer وجود نداشت


</details>
</div>

<div align="right">
  <details>
    <summary><strong><img src="https://github.com/user-attachments/assets/85ac97ea-8365-4eb7-ae23-8432a77e6dc3" alt="Image"> برنامه های اینده</strong></summary>
  
------------------------------------ 

- اگر تمام کارهای پنل به درستی پیش برود و مشکل خاصی نباشد بعدا شاید در صورت امکان مشاهده ایپی های کاربران و بستن و باز کردن ان هم به پنل اضافه کنم که در صورت وجود تانل به صورت 127.0.0.1 نشان میداد.
- ممکن است وارپ با xray از پنل حذف شود چون از خود وایرگارد استفاده میکنیم و به wgcf نسخه پلاس اضافه شود
- بعدا ممکن است تغییراتی در template بدهم
- ممکن است لیست با pagination در بات اضافه شود که کاربران خود را در ان اینترفیس مشاهده کنید و حتما نیاز نباشد که نام ان را تایپ کنید
- ممکن است اضافه کردن کاربر به صورت دسته جمعی هم اضافه کنم
- پس از بررسی پنل در چندین ماه و اطمینان از کارایی ان در شرایط مختلف در صورتی که مشکلی، درسی یا بیماری نداشته باشم، دوست دارم به این پنل Open vpn هم اضافه کنم
- ایده های دیگر در طول زمان در اینجا اضافه میشود


</details>
</div>

--------------------------------

![6348248](https://github.com/Azumi67/PrivateIP-Tunnel/assets/119934376/398f8b07-65be-472e-9821-631f7b70f783)
**آموزش نصب با اسکریپت**
 <div align="right">
  <details>
    <summary><strong><img src="https://github.com/Azumi67/Rathole_reverseTunnel/assets/119934376/fcbbdc62-2de5-48aa-bbdd-e323e96a62b5" alt="Image"> </strong>نصب پنل و بات</summary>

------------------------------------ 

- اجرای اسکریپت دانلود
 
```
sudo apt update && sudo apt install -y curl && apt install git -y && curl -fsSL -o download.sh https://raw.githubusercontent.com/Azumi67/Wireguard-panel/refs/heads/main/download.sh && bash download.sh
```


<p align="right">
  <img src="https://github.com/user-attachments/assets/3c70376b-330b-4ffe-b8f2-60ed18f80a30" alt="Image" />
</p>


- نخست گزینه ها را به ترتیب نصب میکنید تا به گزینه 4 برسید

<p align="right">
  <img src="https://github.com/user-attachments/assets/9a7379c1-f19d-491d-847d-de5342f2c218" alt="Image" />
</p>


- نخست پورت پنل خود را وارد میکنید و سایر موارد را در صورت منابع بهتر در صورت نیاز تغییر میدهید یا به صورت دیفالت به قسمت بعد میروید
- کلید رمز عبور برنامه را وارد نمایید
- در صورت نیاز از tls گزینه yes را وارد نمایید و در صورت نیاز نداشتن به این مورد گزینه No را وارد میکنید و بدون tls استفاده مینمایید
- در صورت وارد کردن yes برای tls، باید ساب دامین و ایمیل خود را وارد نمایید. اطمینان یابید که dns ساب دامین شما به درستی به ایپی سرور شما لینک شده است
- در صورت مشکل نصب، نصب certbot را به صورت دستی انجام دهید و سپس به این مرحله بازگردید
- در صورت استفاده نکردن از tls ادرس داشبورد شما http://publicip:port/home است و در صورت استفاده از tls به صورت https://subdomain:port/home خواهد بود

<p align="right">
  <img src="https://github.com/user-attachments/assets/5f861a94-bb47-4cd2-82ef-cf8c6d78a85c" alt="Image" />
</p>

- قسمت بعدی ست کردن کانفیگ وایرگارد میباشد
- همیشه با wg0 کانفیگ را اغاز کنید و سپس wg1 و wg2
- ایپی پرایوت ورژن 4 باشد و نیازی به ایپی 6 نمیباشد
- پورت و سایر موارد را وارد نمایید.
- در صورت استفاده از فایروال، پورت و رنج پرایوت را باز کنید
<p align="right">
  <img src="https://github.com/user-attachments/assets/c4ce3873-ebd3-435e-8a66-d66a9cf9f260" alt="Image" />
</p>


- این مورد برای اموزش است و تنها پس از نصب اسکریپت و داخل پنل انجام میشود. دقت نمایید که برای استفاده از ربات به زبان انگلیسی، نخست زبان پنل را انگلیسی کنید و سپس ربات را نصب نمایید. فارسی هم به همین صورت میباشد
- برای نصب بات از داخل پنل میتوانید انجام دهید. همان طور که در اسکرین شات مشاهده میکنید توکن باتی که از @BotFather دریافت کردید قرار دهید
- ادرس صفحه هم بر اساس استفاده از tls یا بدون آن خواهد بود. اگر بدون tls است باید http://publicip:port و در صورت آستفاده از tls باید https://subdomain:port قرار دهید
- قسمت بعدی همان کلید api است که از پنل دریافت کرده اید
- قسمت بعدی هم admin chat id رباتی که داخل botfather ساختید را دریافت میکنید . از طریق @userinfobot میتوانید نام ربات خود را بدهید و این مورد را بدست اوردید.
- برای اضافه کردن چندین admin chat id کافی است به این صورت وارد نمایید 676676767 ,67676767 ( استفاده از کاما مانند مثال)
- لطفا تنها از یک بات استفاده نمایید. یا فارسی یا انگلیسی
- سپس گزینه 6 و 7 اسکریپت را نصب کنید و پنل شما اماده است
- در صفحه اصلی ادرس داشبورد خود را مشاهده میکنید

------------------

  </details>
</div>  

 <div align="right">
  <details>
    <summary><strong><img src="https://github.com/Azumi67/Rathole_reverseTunnel/assets/119934376/fcbbdc62-2de5-48aa-bbdd-e323e96a62b5" alt="Image"> </strong>نصب پنل به صورت دستی</summary>

------------------------------------ 

- اجرای دستورات

<div align="left">
  
```
sudo apt update && sudo apt install git -y
cd /usr/local/bin
sudo git clone https://github.com/Azumi67/Wireguard-panel.git
cd /usr/local/bin/Wireguard-panel

sudo apt install -y python3 python3-pip python3-venv git redis nftables iptables wireguard-tools iproute2 \
    fonts-dejavu certbot curl software-properties-common wget

sudo systemctl enable redis-server.service
sudo systemctl start redis-server.service
sudo systemctl status redis-server.service

# creating env

python3 --version
sudo apt update && sudo apt install python3 python3-pip python3-venv
python3 -m venv /usr/local/bin/Wireguard-panel/src/venv
source /usr/local/bin/Wireguard-panel/src/venv/bin/activate
pip install --upgrade pip
pip install python-dotenv python-telegram-bot aiohttp matplotlib qrcode "python-telegram-bot[job-queue]" pyyaml flask-session Flask SQLAlchemy Flask-Limiter Flask-Bcrypt Flask-Caching jsonschema psutil pytz requests pynacl apscheduler redis werkzeug jinja2 fasteners gunicorn pexpect cryptography Pillow arabic-reshaper python-bidi

sudo apt-get install -y libsystemd-dev
deactivate

# permissions

chmod 644 /usr/local/bin/Wireguard-panel/src/config.yaml
chmod -R 600 /usr/local/bin/Wireguard-panel/src/db
chmod -R 700 /usr/local/bin/Wireguard-panel/src/backups
chmod 644 /usr/local/bin/Wireguard-panel/src/telegram/telegram.yaml
chmod 644 /usr/local/bin/Wireguard-panel/src/telegram/config.json
chmod 644 /usr/local/bin/Wireguard-panel/src/install_progress.json
chmod 644 /usr/local/bin/Wireguard-panel/src/api.json
chmod 744 /usr/local/bin/Wireguard-panel/src/install_telegram.sh
chmod 744 /usr/local/bin/Wireguard-panel/src/install_telegram-fa.sh
chmod -R 644 /usr/local/bin/Wireguard-panel/src/static/fonts
chmod -R 644 /usr/local/bin/Wireguard-panel/src/telegram/static/fonts
chmod -R 755 /etc/wireguard

```

- Flask & gunicorn configuration :

```
nano /usr/local/bin/Wireguard-panel/src/config.yaml

###
flask:
  port: 8443
  tls: true
  cert_path: "/etc/letsencrypt/live/subdomain.com/fullchain.pem"
  key_path: "/etc/letsencrypt/live/subdomain.com/privkey.pem"
  secret_key: "azumi"
  debug: false

gunicorn:
  workers: 2
  threads: 1
  loglevel: "info"
  timeout: 120
  accesslog: ""
  errorlog: ""

wireguard:
  config_dir: "/etc/wireguard"
##

```

- Wireguard configuration :

```
nano /etc/wireguard/wg0.conf

##
[Interface]
Address = 166.66.66.1/25
ListenPort = 20821
PrivateKey = aBY+lbhuOlBknLDDi2MbI11LZKEDGOSsvIbWQDuCSX0=
MTU = 1380
DNS = 1.1.1.1

PostUp = iptables -I INPUT -p udp --dport 20821 -j ACCEPT
PostUp = iptables -I FORWARD -i eth0 -o wg0 -j ACCEPT
PostUp = iptables -I FORWARD -i wg0 -j ACCEPT
PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

PostDown = iptables -D INPUT -p udp --dport 20821 -j ACCEPT
PostDown = iptables -D FORWARD -i eth0 -o wg0 -j ACCEPT
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT
PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

##

Commands for generating private & pub key :
wg genkey | tee privatekey
cat privatekey | wg pubkey > publickey


```

- Wireguard panel service
```
nano /etc/systemd/system/wireguard-panel.service

##
[Unit]
Description=Wireguard Panel
After=network.target

[Service]
User=root
WorkingDirectory=/usr/local/bin/Wireguard-panel/src
ExecStart=/usr/local/bin/Wireguard-panel/src/venv/bin/python3 /usr/local/bin/Wireguard-panel/src/app.py
Restart=always
Environment=PATH=/usr/local/bin/Wireguard-panel/src/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=LANG=en_US.UTF-8
Environment=LC_ALL=en_US.UTF-8

[Install]
WantedBy=multi-user.target

##
```
------------------------------------ 

  </details>
</div>  

---------------
![check](https://github.com/user-attachments/assets/723872d1-1594-4d31-b48b-2b1c41adfaa9)
**اسکرین شات**
<div style="direction: rtl; text-align: right;">
  <details>
    <summary style="font-size: 14px; padding: 5px;">پنل</summary>
    <p style="margin: 0; text-align: right;">
     <p align="right">
      <img src="https://github.com/user-attachments/assets/cb754472-6a4a-4511-acde-b037737b600f" alt="menu screen" style="max-width: 100px; height: auto;" />
    </p>
  </details>

  <details>
    <summary style="font-size: 14px; padding: 5px;">ساخت کاربر</summary>
    <p style="margin: 0; text-align: right;">
     <p align="right">
      <img src="https://github.com/user-attachments/assets/d8b799b5-8825-4079-bfbb-e68c9fa1c7c5" alt="menu screen" style="max-width: 100px; height: auto;" />
    </p>
  </details>

  <details>
    <summary style="font-size: 14px; padding: 5px;">باکس کاربر</summary>
    <p style="margin: 0; text-align: right;">
     <p align="right">
      <img src="https://github.com/user-attachments/assets/ec328904-6e78-4536-a08b-600f3a0c6a64" alt="menu screen" style="max-width: 100px; height: auto;" />
    </p>
  </details>

  <details>
    <summary style="font-size: 14px; padding: 5px;">بات</summary>
    <p style="margin: 0; text-align: right;">
     <p align="right">
      <img src="https://github.com/user-attachments/assets/33a595b4-8667-4507-a181-764101d6924f" alt="menu screen" style="max-width: 100px; height: auto;" />
    </p>
  </details>

  <details>
    <summary style="font-size: 14px; padding: 5px;">ساخت کاربر بات</summary>
    <p style="margin: 0; text-align: right;">
     <p align="right">
      <img src="https://github.com/user-attachments/assets/dc478252-de84-4173-9aa8-9233385dbdbd" alt="menu screen" style="max-width: 100px; height: auto;" />
    </p>
  </details>

  <details>
    <summary style="font-size: 14px; padding: 5px;">نمایش template کاربر</summary>
    <p style="margin: 0; text-align: right;">
     <p align="right">
      <img src="https://github.com/user-attachments/assets/022e4cb5-2c66-41b0-bd3d-17f27047a3b1" alt="menu screen" style="max-width: 100px; height: auto;" />
    </p>
  </details>

  <details>
    <summary style="font-size: 14px; padding: 5px;">منوی کاربر بات</summary>
    <p style="margin: 0; text-align: right;">
     <p align="right">
      <img src="https://github.com/user-attachments/assets/c8fd5c11-74a9-4393-8977-3431e4f76f73" alt="menu screen" style="max-width: 100px; height: auto;" />
    </p>
  </details>
</div>


-----------------------------------------------------

![R (a2)](https://github.com/Azumi67/PrivateIP-Tunnel/assets/119934376/716fd45e-635c-4796-b8cf-856024e5b2b2)
**اسکریپت دانلود**
----------------


```
sudo apt update && sudo apt install -y curl && apt install git -y && curl -fsSL -o download.sh https://raw.githubusercontent.com/Azumi87/Wireguard-panel/refs/heads/main/download.sh && bash download.sh

```

- باز فراخوانی اسکریپت
```
chmod +x /usr/local/bin/Wireguard-panel/src/setup.sh
wire
```

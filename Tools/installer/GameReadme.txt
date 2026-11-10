INSTAGIB ARENA  -  Windows build
==================================

HOW TO RUN
  Installed with the setup wizard:  start "Instagib Arena" from the desktop icon or the Start menu.
  Unzipped by hand:                 double-click InstagibArena.exe (do not run it from inside the zip).

  If Windows shows a blue "Windows protected your PC" screen, click "More info" and then "Run anyway".
  (The game is not signed, so Windows does not know the publisher.)
  If you get an error about VCRUNTIME or a missing DLL, install  Engine\Extras\Redist\en-us\vc_redist.x64.exe
  once and try again. You do not need Unreal Engine to play.

CONTROLS
  W A S D        move
  Mouse          look
  Space          jump (press twice for a double jump)
  Double-tap W/A/S/D   dodge in that direction
  Dodge near a wall while in the air   wall dodge
  Left mouse     fire the instagib rifle (one hit kills)
  Tab            scoreboard
  Esc            pause menu (resume, settings, leave the match, quit)

MAIN MENU
  QUICK PLAY     start a match with your last settings
  CUSTOM GAME    game type (Free For All or Team Deathmatch), map, bots (2 to 10) and their skill, score and time limit
  MULTIPLAYER    host a game, or join one with the host's address
  CHARACTER      pick one of 15 characters, with a live 3D preview
  SETTINGS       player name, music and effects volume, mouse sensitivity, field of view, fullscreen or windowed
  Esc goes back one screen. The arrow keys and Enter work too. Your choices are remembered.

PLAYING WITH FRIENDS
  Same network (home Wi-Fi / LAN):
    - One player opens MULTIPLAYER > HOST A GAME, sets the rules and clicks HOST GAME.
      The screen shows the address to give to friends.
    - Everyone else opens MULTIPLAYER > JOIN A GAME, types that address and clicks JOIN GAME.
    - If Windows asks whether to allow the game through the firewall, click Allow.

  Over the internet:
    - Easiest: all players install Tailscale or ZeroTier (free) and join the same virtual network,
      then use the host's Tailscale/ZeroTier address in the Join screen.
    - Or the host forwards UDP port 7777 on their router to their PC and shares their public IP.

  If a connection fails or is lost, the menu says so on the Join screen.

NOTES
  - Windows only. Work in progress: expect rough edges.
  - Everything in this game (models, sounds, music) is either from Unreal Engine's free starter content
    or generated for this project.


=====================================================================
אינסטגיב ארינה  -  גרסת Windows
=====================================================================

איך מפעילים
  אחרי התקנה עם אשף ההתקנה:  מפעילים את "Instagib Arena" מהסמל בשולחן העבודה או מתפריט התחל.
  אם פתחתם zip ידנית:         לוחצים פעמיים על InstagibArena.exe (לא מפעילים מתוך הקובץ הדחוס).

  אם Windows מציג מסך כחול "Windows protected your PC", לוחצים "More info" ואז "Run anyway".
  (המשחק לא חתום, ולכן Windows לא מכיר את היוצר.)
  אם מופיעה שגיאה על VCRUNTIME או קובץ DLL חסר, מתקינים פעם אחת את
  Engine\Extras\Redist\en-us\vc_redist.x64.exe  ומנסים שוב. אין צורך ב-Unreal Engine כדי לשחק.

מקשים
  W A S D          תנועה
  עכבר             הסתכלות
  רווח             קפיצה (פעמיים - קפיצה כפולה)
  לחיצה כפולה על W/A/S/D   דודג' לכיוון הזה
  דודג' ליד קיר באוויר     קפיצת קיר
  כפתור שמאלי בעכבר         ירי ברובה (פגיעה אחת הורגת)
  Tab               לוח תוצאות
  Esc               תפריט השהיה (המשך, הגדרות, עזיבת המשחק, יציאה)

התפריט הראשי
  QUICK PLAY     מתחילים משחק עם ההגדרות האחרונות
  CUSTOM GAME    סוג משחק, מפה, בוטים (2 עד 10) ורמתם, הגבלת ניקוד וזמן
  MULTIPLAYER    לארח משחק או להצטרף לכתובת של מארח
  CHARACTER      בחירה מ-15 דמויות, עם תצוגה תלת-ממדית
  SETTINGS       שם שחקן, עוצמת מוזיקה ואפקטים, רגישות עכבר, שדה ראייה, מסך מלא או חלון
  Esc חוזר מסך אחד אחורה. גם החצים ו-Enter עובדים. הבחירות שלכם נשמרות.

לשחק עם חברים
  באותה רשת (ביתית):
    - שחקן אחד נכנס ל-MULTIPLAYER > HOST A GAME, קובע חוקים ולוחץ HOST GAME.
      במסך מופיעה הכתובת שצריך לתת לחברים.
    - כל השאר נכנסים ל-MULTIPLAYER > JOIN A GAME, כותבים את הכתובת ולוחצים JOIN GAME.
    - אם Windows שואל אם לאפשר את המשחק בחומת האש - לוחצים Allow.

  דרך האינטרנט:
    - הכי קל: כולם מתקינים Tailscale או ZeroTier (חינמיים) ומצטרפים לאותה רשת וירטואלית,
      ומשתמשים בכתובת של המארח מתוכנה זו במסך ה-Join.
    - או: המארח מפנה פורט UDP 7777 בנתב אל המחשב שלו ומשתף את כתובת ה-IP הציבורית שלו.

  אם החיבור נכשל או נותק, התפריט אומר זאת במסך ה-Join.

הערות
  - Windows בלבד. המשחק בפיתוח, צפויים פגמים.
  - כל המודלים, הצלילים והמוזיקה הם מתוכן ההתחלה החינמי של Unreal Engine או נוצרו עבור הפרויקט.

INSTAGIB ARENA  -  Windows build
==================================

HOW TO RUN
  1. Unzip the whole folder (do not run the game from inside the zip).
  2. Double-click  InstagibArena.exe
  3. If Windows shows a blue "Windows protected your PC" screen, click "More info" and then "Run anyway".
     (The game is not signed, so Windows does not know the publisher.)
  4. If you get an error about VCRUNTIME or a missing DLL, install  Engine\Extras\Redist\en-us\vc_redist.x64.exe
     once and try again.

CONTROLS
  W A S D        move
  Mouse          look
  Space          jump (press twice for a double jump)
  Double-tap W/A/S/D   dodge in that direction
  Dodge near a wall while in the air   wall dodge
  Left mouse     fire the instagib rifle (one hit kills)
  Tab            scoreboard
  Esc            back to the main menu

MENU
  Game type (Free For All or Team Deathmatch), map (4 maps), character (15, with a live preview),
  number of bots (2 to 10) and their skill, score limit, time limit, music volume and effects volume.
  The volumes are remembered for next time.

PLAYING WITH FRIENDS
  Same network (home Wi-Fi / LAN):
    - One player clicks "Host LAN game" in the menu.
    - The host finds their IP address (open Command Prompt, type  ipconfig,  look for "IPv4 Address").
    - Everyone else types that address in the box next to "Join" and clicks Join.
    - If Windows asks whether to allow the game through the firewall, click Allow.

  Over the internet:
    - Easiest: all players install Tailscale or ZeroTier (free) and join the same virtual network,
      then use the host's Tailscale/ZeroTier address in the Join box.
    - Or the host forwards UDP port 7777 on their router to their PC and shares their public IP.

  The host chooses the game type, map, bots and limits before clicking Host.
  Each player picks their own character in the menu before joining.

NOTES
  - Windows only. Work in progress: expect rough edges.
  - Everything in this game (models, sounds, music) is either from Unreal Engine's free starter content
    or generated for this project.


=====================================================================
אינסטגיב ארינה  -  גרסת Windows
=====================================================================

איך מפעילים
  1. פותחים את כל התיקייה מה-zip (לא מפעילים מתוך הקובץ הדחוס).
  2. לוחצים פעמיים על  InstagibArena.exe
  3. אם Windows מציג מסך כחול "Windows protected your PC", לוחצים "More info" ואז "Run anyway".
     (המשחק לא חתום, ולכן Windows לא מכיר את היוצר.)
  4. אם מופיעה שגיאה על VCRUNTIME או קובץ DLL חסר, מתקינים פעם אחת את
     Engine\Extras\Redist\en-us\vc_redist.x64.exe  ומנסים שוב.

מקשים
  W A S D          תנועה
  עכבר             הסתכלות
  רווח             קפיצה (פעמיים - קפיצה כפולה)
  לחיצה כפולה על W/A/S/D   דודג' לכיוון הזה
  דודג' ליד קיר באוויר     קפיצת קיר
  כפתור שמאלי בעכבר         ירי ברובה (פגיעה אחת הורגת)
  Tab               לוח תוצאות
  Esc               חזרה לתפריט הראשי

התפריט
  סוג משחק (Free For All או Team Deathmatch), מפה (4 מפות), דמות (15, עם תצוגה מקדימה),
  מספר בוטים (2 עד 10) ורמתם, הגבלת ניקוד, הגבלת זמן, עוצמת מוזיקה ועוצמת אפקטים.
  עוצמות הקול נשמרות להפעלה הבאה.

לשחק עם חברים
  באותה רשת (ביתית):
    - שחקן אחד לוחץ "Host LAN game" בתפריט.
    - המארח מוצא את כתובת ה-IP שלו (בחלון Command Prompt כותבים ipconfig ומחפשים IPv4 Address).
    - כל השאר כותבים את הכתובת בתיבה שליד "Join" ולוחצים Join.
    - אם Windows שואל אם לאפשר את המשחק בחומת האש - לוחצים Allow.

  דרך האינטרנט:
    - הכי קל: כולם מתקינים Tailscale או ZeroTier (חינמיים) ומצטרפים לאותה רשת וירטואלית,
      ומשתמשים בכתובת של המארח מתוכנה זו בתיבת ה-Join.
    - או: המארח מפנה פורט UDP 7777 בנתב אל המחשב שלו ומשתף את כתובת ה-IP הציבורית שלו.

  המארח בוחר סוג משחק, מפה, בוטים והגבלות לפני הלחיצה על Host.
  כל שחקן בוחר דמות בתפריט לפני שמצטרף.

הערות
  - Windows בלבד. המשחק בפיתוח, צפויים פגמים.
  - כל המודלים, הצלילים והמוזיקה הם מתוכן ההתחלה החינמי של Unreal Engine או נוצרו עבור הפרויקט.

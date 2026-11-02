========================================================================
Optima MTK Tool Pro - Dossier Outils Embarqués (tools/)
========================================================================

Ce dossier est dédié aux exécutables et bibliothèques de communication mobile :
  - adb.exe
  - fastboot.exe
  - AdbWinApi.dll
  - AdbWinUsbApi.dll

Priorité de détection dans Optima MTK Tool :
  1. tools\adb.exe (Dossier local du projet - Priorité maximale)
  2. platform-tools\adb.exe
  3. Variables d'environnement PATH système
  4. Android SDK (%LOCALAPPDATA%\Android\Sdk\platform-tools)
  5. C:\adb ou C:\platform-tools

Pour un déploiement autonome en atelier sans installation préalable d'Android SDK,
placez adb.exe et fastboot.exe ainsi que leurs dépendances DLL dans ce dossier.
========================================================================

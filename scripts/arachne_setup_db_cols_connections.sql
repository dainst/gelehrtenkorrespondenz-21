
ALTER TABLE `buch_elemente`
    ADD COLUMN `FS_Buch2ID` mediumint(8) unsigned DEFAULT NULL,
    ADD KEY `FS_Buch2ID` (`FS_Buch2ID`);

ALTER TABLE personobjekte
    ADD COLUMN `Rolle` varchar(255) DEFAULT NULL,
    ADD KEY `Rolle` (`Rolle`);

INSERT INTO `Sem_Verknuepfungen` SET
    `Teil1` = 'Buch',
    `Teil2` = 'Buch2',
    `Tabelle` = 'buch_elemente',
    `Befehl` = 'insert',
    `Felder` = 'KommentarBuchElement|Kommentar',
    `Ersetzen` = 0,
    `SelfConnection` = 'Buch',
    `Type` = 'UnDirectedSelfconnection',
    `StandardCIDOCConnectionType` = 'P67_refers_to/P67i_is_referred_to_by',
    `GuiEnabled` = 1;

UPDATE Sem_Verknuepfungen SET Felder = CONCAT(Felder, ',Rolle|Rolle') WHERE Tabelle = 'personobjekte' AND Felder > '';

# To undo these changes:
# ALTER TABLE `buch_elemente` DROP COLUMN `FS_Buch2ID`;
# ALTER TABLE `personobjekte` DROP COLUMN `Rolle`;
# DELETE FROM `Sem_Verknuepfungen` WHERE `Teil1` = 'Buch' AND `Teil2` = 'Buch2' AND `Tabelle` = 'buch_elemente';
# UPDATE Sem_Verknuepfungen SET Felder = REPLACE(Felder, ',Rolle|Rolle', '') WHERE Tabelle = 'personobjekte';

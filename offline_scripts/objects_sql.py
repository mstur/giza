# Object display data 
# TODO: Get Primary Image URL (need an image server first)
OBJECTS = """
SELECT Objects.ObjectID as ID, Objects.ObjectNumber, Objects.ObjectStatusID, Objects.ClassificationID, Objects.ObjectName + ',,' as ObjectOwnerDetails,
Objects.Dated as EntryDate, replace(replace(ObjTitles.Title, char(10), ''), char(13), ' ') AS Title, Objects.Medium + ',,' as Medium, 
Objects.Dimensions + ',,' as Dimensions, Objects.CreditLine, Objects.Description + ',,' AS Description, Objects.Provenance, 
Objects.PubReferences + ',,' AS PubReferences, Objects.Notes + ',,' AS Notes, Objects.Chat + ',,' as DiaryTranscription, 
Objects.CuratorialRemarks + ',,' AS Remarks, ObjPkgList.objectnumber as FieldNumber
FROM Objects 
LEFT JOIN ObjTitles on Objects.ObjectID=ObjTitles.ObjectID
LEFT JOIN ObjPkgList on Objects.ObjectID=ObjPkgList.objectid
WHERE Objects.PublicAccess = 1
AND Objects.ObjectID >= 0
AND ObjPkgList.objectnumber IS NOT NULL
ORDER BY Objects.ObjectID
"""

# Related Sites for all Objects
RELATED_SITES = """
SELECT Objects.ObjectID as ID, SiteObjXrefs.SiteID, 
Sites.SiteName, Sites.SiteNumber, Objects.ClassificationID
FROM Objects 
LEFT JOIN SiteObjXrefs ON Objects.ObjectID=SiteObjXrefs.ObjectID
LEFT JOIN Sites ON SiteObjXrefs.SiteID=Sites.SiteID
WHERE Sites.IsPublic = 1
AND Objects.PublicAccess = 1
ORDER BY Objects.ObjectID
"""

# Related Constituents (Modern and Ancient) for all Objects
RELATED_CONSTITUENTS = """
SELECT ConXrefs.ID as ID, Roles.Role, ConXrefDetails.ConstituentID, Constituents.ConstituentTypeID, 
Constituents.DisplayName, Constituents.DisplayDate, Objects.ClassificationID
FROM ConXrefs 
LEFT JOIN ConXrefDetails on ConXrefs.ConXrefID=ConXrefDetails.ConXrefID
LEFT JOIN Constituents on ConXrefDetails.ConstituentID=Constituents.ConstituentID
LEFT JOIN Roles on ConXrefs.RoleID=Roles.RoleID
LEFT JOIN Objects on ConXrefs.ID=Objects.ObjectID
WHERE ConXrefs.TableID=108
AND Constituents.Active=1
AND ConXrefDetails.Unmasked=1
ORDER BY ConXrefs.ID
"""

# Related Published Documents for all Objects 
RELATED_PUBLISHED = """
SELECT RefXrefs.ID as ID, ReferenceMaster.ReferenceID, ReferenceMaster.BoilerText, Objects.ClassificationID
FROM RefXrefs 
LEFT JOIN ReferenceMaster on RefXrefs.ReferenceID=ReferenceMaster.ReferenceID
LEFT JOIN Objects on RefXrefs.ID=Objects.ObjectID
WHERE RefXrefs.TableID=108
ORDER BY RefXrefs.ID
"""

RELATED_UNPUBLISHED = """
SELECT Associations.ID1 as ID, Associations.ID2 as UnpublishedID, 
replace(replace(ObjTitles.Title, char(10), ''), char(13), ' ') AS UnpublishedTitle, Objects.ClassificationID
FROM Associations 
LEFT JOIN ObjTitles on Associations.ID2=ObjTitles.ObjectID
LEFT JOIN Objects on Associations.ID1=Objects.ObjectID
WHERE TableID=108 
AND RelationshipID=6
ORDER BY ID1
"""

# Related Media for all Objects
RELATED_MEDIA = """
SELECT MediaXrefs.ID as ID, MediaMaster.MediaMasterID, Objects.ClassificationID
FROM MediaXrefs 
LEFT JOIN MediaMaster on MediaXrefs.MediaMasterID=MediaMaster.MediaMasterID
LEFT JOIN MediaRenditions on MediaMaster.MediaMasterID=MediaRenditions.MediaMasterID
LEFT JOIN Objects on MediaXrefs.ID=Objects.ObjectID
WHERE MediaXrefs.TableID=108
AND PublicAccess=1
AND MediaRenditions.MediaTypeID=1
ORDER BY MediaXrefs.ID
"""
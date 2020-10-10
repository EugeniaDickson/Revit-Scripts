import Autodesk.Revit.DB as DB
import Autodesk.Revit.UI as UI
import pyrevit
import System
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from pyrevit import DB, forms, revit, script
from pyrevit.forms import *
from rpw.ui.forms import *
from System.Collections.Generic import *

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
uiApp = uidoc.Application

__author__ = 'Eugenia Dickson'
__name__ = 'Align Multiple Viewports'
__doc__ = 'Select a source sheet: \n' \
            'Select multiple destination sheets: \n' \
            'All viewports on destination sheets are aligned '\
            'to the xy point of the viewports on the source sheet.'

def hide_objects(obj, cat1, cat2):
    obj.HideCategoriesTemporary(List[DB.ElementId](cat1))
    obj.HideElementsTemporary(List[DB.ElementId](cat2))

def unhide_objects(obj):
    doc.GetElement(obj.ViewId).DisableTemporaryViewMode(
                DB.TemporaryViewMode.TemporaryHideIsolate)

def main():
    sourceSheet = forms.select_sheets(multiple=False)
    if sourceSheet is None:
        script.exit()

    #GETTING SOURCE VIEWPORTS COORDINATES
    sourceViewportIds = sourceSheet.GetAllViewports()
    sourceViewports = []
    sourceViewportNums = []
    sourcePts = []
    for i in sourceViewportIds:
        sourceViewports.append(doc.GetElement(i))
        sourcePts.append(doc.GetElement(i).GetBoxCenter())
        sourceViewportNums.append(doc.GetElement(i).get_Parameter(BuiltInParameter.VIEWPORT_DETAIL_NUMBER).AsString())

    locationDict = {}
    if len(sourceViewports) >= 1:
        locationDict = dict(zip(sourceViewportNums, sourcePts))
    elif len(sourceViewports) < 1:
        forms.alert('No viewport on selected source sheet.')
        script.exit()
    if sourceViewports is None:
        script.exit()

    #GETTING VIEWPORTS ON THE SPECIFIED SHEET
    destSheets = forms.select_sheets()
    if destSheets is None:
        script.exit()

    allCategories = doc.Settings.Categories
    catIds = []
    # Filter categories to just model categories + Matchlines and Scope Boxes
    for c in allCategories:
        if c.CategoryType == DB.CategoryType.Annotation:
            catIds.append(c.Id)
        elif c.CategoryType == DB.CategoryType.Model:
            if c.Name == 'Lighting Fixtures':
                catIds.append(c.Id)

    linkInstances = DB.FilteredElementCollector(doc)\
        .OfClass(DB.RevitLinkInstance)\
        .WhereElementIsNotElementType()\
        .ToElements()

    linkInstanceIds = []
    for link in linkInstances:
        linkInstanceIds.append(link.Id)

    #APPLYING SOURCE VIEW COORDINATES TO DESTINATION VIEWS
    with revit.Transaction('Align Multiple Viewports'):
        for svp in sourceViewports:
            view = doc.GetElement(svp.ViewId)
            hide_objects(view, catIds, linkInstanceIds)
        for sheet in destSheets:
            destViewports = []
            temp = sheet.GetAllViewports()
            for i in temp:
                destViewports.append(doc.GetElement(i))
            for dvp in destViewports:
                view = doc.GetElement(dvp.ViewId)
                hide_objects(view, catIds, linkInstanceIds)
            if len(destViewports) == len(sourceViewports):
                for vp in destViewports:
                    viewNumber = vp.get_Parameter(BuiltInParameter.VIEWPORT_DETAIL_NUMBER).AsString()
                    mappedLocation = locationDict.get(viewNumber, None)
                    vp.SetBoxCenter(mappedLocation)
                    unhide_objects(vp)
            else:
                forms.alert('Numbers of viewports don\'t match.')
        for svp in sourceViewports:
            unhide_objects(svp)

main()
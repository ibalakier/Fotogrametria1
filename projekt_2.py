#Automatyzacja przetwarzania zdjęć lotniczych z drona w programie Agisoft Metashape

import Metashape
import sys
import glob 
import numpy as np

def BatchImagesImporting(ImageFormat,Document):
    path=Metashape.app.getExistingDirectory('Please define the image path:')
    if len(path)==0:
        return
    print("Batch Images Importing...",path)
    print(path)
    images=glob.glob(path+r'\*.'+ImageFormat)
    print(images)
    Chunk=Document.addChunk()
    Chunk.label="Chunk 1"
    Chunk.addPhotos(images)
    ImagesOrientation(Chunk)
	
def ImagesOrientation(Chunk):
    for frame in Chunk.frames:
        frame.matchPhotos(downscale=2,generic_preselection=False,reference_preselection=True)
    Chunk.alignCameras()

def DefineBundleAdjustmentParameters(Chunk,MarkerLocationAccuracy=Metashape.Vector([0.02,0.02,0.05]),CameraLocationAccuracy=Metashape.Vector([100,100,100]),CameraRotationAccuracy=Metashape.Vector([100,100,100]),TiePointAccuracy=2000,MarkerProjectionAccuracy=0.1,ScalebareAccuracy=0.2):
    Chunk.marker_location_accuracy=MarkerLocationAccuracy
    Chunk.marker_projection_accuracy=MarkerProjectionAccuracy
    Chunk.scalebar_accuracy=ScalebareAccuracy
    Chunk.tiepoint_accuracy=TiePointAccuracy
    Chunk.camera_rotation_accuracy=CameraRotationAccuracy
    Chunk.camera_location_accuracy=CameraLocationAccuracy
    print('ok')
    
def ExportCameras(Chunk):
    File=Metashape.app.getSaveFileName('Export cameras', filter="XML (*.xml);;OmegaPhiKappa with Rotation Matrix (*.opk);;Bundler (*.out)")
    if File[-3:]=="xml":
        Chunk.exportCameras(File, format=Metashape.CamerasFormatXML,save_markers=True)
    elif File[-3:]=="opk":
        Chunk.exportCameras(File, format=Metashape.CamerasFormatOPK)
    elif File[-3:]=="out":
        Chunk.exportCameras(File, format=Metashape.CamerasFormatBundler)
    else:
        Chunk.exportCameras(File, format=Metashape.CamerasFormatOPK)

def getMarker(Chunk, Label):
    for marker in Chunk.markers:
        if marker.label == Label:
            return marker
    return None

def getCamera(Chunk, Label):
    for camera in Chunk.cameras:
        if camera.label == Label:
            return camera
    return None

def ImportTraces(Chunk):
    repx = []
    repy = []
    File = Metashape.app.getOpenFileName('Traces',filter="*.txt")
    if len(File) == 0:
        return
    File = open(File, "r")
    content = File.readlines()
    
    for i in content:
        mark, cam, x_std, y_std, xfc, yfc = i.split()
        x=float(x_std)
        y=float(y_std)
        repx.append(x)
        repy.append(y)
    stdx=np.std(repx)
    stdy=np.std(repy)
    # print(content[0])
    if len(content[0].split()) == 6:
        for line in content:
            MarkerLabel, CameraLabel , ImageFormat, Document, XFeatureCoordinates, YFeatureCoordinates = line.split()
            marker = getMarker(Chunk, MarkerLabel)
            if not marker:
                marker = Chunk.addMarker()
                marker.label = MarkerLabel
            camera = getCamera(Chunk, CameraLabel)
            if not camera:
                print(CameraLabel + " camera not found in project")
                continue
            if abs(stdx) <= 2.5 and abs(stdy) <= 2.5:
                marker.projections[camera] = Metashape.Marker.Projection(Metashape.Vector([float(XFeatureCoordinates), float(YFeatureCoordinates)]), True)
            

def ExportMarkers(Chunk):
    File = Metashape.app.getSaveFileName('Export filtered traces',filter="*.txt")
    File = open(File, 'w')
    for marker in Chunk.markers:
        for camera in Chunk.cameras:
            if camera.enabled == 1:
                Point2D = marker.projections[camera]
                if Point2D is not None:
                    ReprojectionError = camera.project(marker.position)-marker.projections[camera].coord
                    File.write(marker.label)
                    File.write(' ')
                    File.write(camera.label)
                    File.write(' ')
                    File.write('%f ' % ReprojectionError[0])
                    File.write('%f ' % ReprojectionError[1])
                    File.write('%f ' % marker.projections[camera].coord[0])
                    File.write('%f ' % marker.projections[camera].coord[1])
                    File.write('\n')
    File.close()   

def CoordinateSystem(Chunk,arg):
    if arg == "yes":
        target_crs = Metashape.CoordinateSystem("EPSG::2180") 
        for camera in Chunk.cameras:
            camera.reference.location = target_crs.project(Chunk.crs.unproject(camera.reference.location))
        Chunk.crs = target_crs
        print("Aktualny układ EPSG::2180")
    else: 
        target_crs = Metashape.CoordinateSystem("EPSG::4326") 
        for camera in Chunk.cameras:
            camera.reference.location = target_crs.project(Chunk.crs.unproject(camera.reference.location))
        Chunk.crs = target_crs
        print("Aktualny układ EPSG::4326") 
   
def ImportUAV(Chunk):
    Chunk.importReference('osnowa_UAV.txt', Metashape.ReferenceFormatCSV, delimiter=',',create_markers=True)
    Chunk.updateTransform()


def main():
    Document=Metashape.app.document
    Chunk=Document.chunk
    ImageFormat=sys.argv[1]
    Arg2=sys.argv[2]
    Arg3=sys.argv[3]
    Metashape.app.removeMenuItem("Image processing")
    Metashape.app.addMenuItem("Image processing/Batch Images Importing",lambda:BatchImagesImporting(ImageFormat,Document))
    Metashape.app.addMenuItem("Image processing/Image Orientation",lambda:ImagesOrientation)
    Metashape.app.addMenuItem("Image processing/Define Bundle Adjustment Parameters",lambda:DefineBundleAdjustmentParameters(Chunk))
    Metashape.app.addMenuItem("Image processing/Export Cameras",lambda:ExportCameras(Chunk))
    Metashape.app.addMenuItem("Image processing/Export Markers",lambda:ExportMarkers(Chunk))
    Metashape.app.addMenuItem("Image processing/Import Traces",lambda:ImportTraces(Chunk))
    Metashape.app.addMenuItem("Image processing/Coordinate System",lambda:CoordinateSystem(Chunk,Arg3))
    Metashape.app.addMenuItem("Image processing/Import UAV",lambda:ImportUAV(Chunk))


if __name__=="__main__":
	main()
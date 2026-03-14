# execute-code Patterns

## Document and Object Inspection

```python
# Get document info as JSON
import FreeCAD, json
doc = FreeCAD.ActiveDocument
print(json.dumps({
    "name": doc.Name,
    "objects": [{"name": o.Name, "type": o.TypeId} for o in doc.Objects]
}))
```

## PartDesign Workflow

```python
# Create Body and Sketch
import FreeCAD
doc = FreeCAD.ActiveDocument
body = doc.addObject("PartDesign::Body", "Body")
sketch = body.newObject("Sketcher::SketchObject", "Sketch")
sketch.MapMode = "FlatFace"
doc.recompute()
print(body.Name)
```

```python
# Add geometry to a Sketch (rectangle)
import FreeCAD, Sketcher, Part
doc = FreeCAD.ActiveDocument
sketch = doc.getObject("Sketch")
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(0,0,0), FreeCAD.Vector(20,0,0)))
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(20,0,0), FreeCAD.Vector(20,10,0)))
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(20,10,0), FreeCAD.Vector(0,10,0)))
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(0,10,0), FreeCAD.Vector(0,0,0)))
doc.recompute()
print("sketch updated")
```

```python
# Pad (extrude) a sketch
import FreeCAD
doc = FreeCAD.ActiveDocument
pad = doc.Body.newObject("PartDesign::Pad", "Pad")
pad.Profile = doc.Sketch
pad.Length = 10.0  # mm
doc.recompute()
print(pad.Name)
```

```python
# Pocket (cut) operation
import FreeCAD
doc = FreeCAD.ActiveDocument
pocket = doc.Body.newObject("PartDesign::Pocket", "Pocket")
pocket.Profile = doc.Sketch001
pocket.Length = 5.0
doc.recompute()
print(pocket.Name)
```

```python
# Fillet edges
import FreeCAD
doc = FreeCAD.ActiveDocument
fillet = doc.Body.newObject("PartDesign::Fillet", "Fillet")
fillet.Base = (doc.Pad, ["Edge1", "Edge2"])
fillet.Radius = 2.0
doc.recompute()
print(fillet.Name)
```

## Export

```python
# STL export
import FreeCAD, Mesh
doc = FreeCAD.ActiveDocument
obj = doc.getObject("Body")
Mesh.export([obj], "/tmp/output.stl")
print("exported to /tmp/output.stl")
```

```python
# STEP export
import FreeCAD, Part
doc = FreeCAD.ActiveDocument
obj = doc.getObject("Body")
Part.export([obj], "/tmp/output.step")
print("exported to /tmp/output.step")
```

## View and Camera

```python
# Reset to isometric view + fit all
import FreeCADGui
view = FreeCADGui.ActiveDocument.ActiveView
view.viewIsometric()
view.fitAll()
print("view reset")
```

```python
# Save screenshot to file
import FreeCADGui
view = FreeCADGui.ActiveDocument.ActiveView
view.saveImage("/tmp/screenshot.png", 1920, 1080, "Current")
print("saved")
```

## Diagnostics

```python
# FreeCAD version
import FreeCAD
print(FreeCAD.Version())
```

```python
# List available workbenches
import FreeCADGui, json
print(json.dumps(list(FreeCADGui.listWorkbenches().keys())))
```

```python
# Get all properties of an object (debug)
import FreeCAD, json
doc = FreeCAD.ActiveDocument
obj = doc.getObject("Body")
props = {}
for p in obj.PropertiesList:
    try:
        v = getattr(obj, p)
        json.dumps(v)
        props[p] = v
    except (TypeError, ValueError):
        props[p] = str(v)
print(json.dumps(props))
```

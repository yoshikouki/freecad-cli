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

### Body and Sketch Creation

```python
# Create Body and attach Sketch to XY plane
import FreeCAD
doc = FreeCAD.ActiveDocument
body = doc.addObject("PartDesign::Body", "Body")
sketch = body.newObject("Sketcher::SketchObject", "Sketch")

# Attach to XY plane via Body's Origin
for feat in body.Origin.OriginFeatures:
    if "XY" in feat.Label:
        sketch.AttachmentSupport = [(feat, "")]
        sketch.MapMode = "FlatFace"
        break
doc.recompute()
print(body.Name)
```

### Sketch Geometry

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
# Add geometry (regular polygon — hexagon example)
import FreeCAD, Part, math
doc = FreeCAD.ActiveDocument
sketch = doc.getObject("Sketch")
n_sides = 6
hex_width = 35.0  # flat-to-flat distance
circumradius = hex_width / (2 * math.cos(math.radians(180 / n_sides)))
points = []
for i in range(n_sides):
    angle = math.radians(360 / n_sides * i + 30)
    points.append(FreeCAD.Vector(circumradius * math.cos(angle), circumradius * math.sin(angle), 0))

line_ids = []
for i in range(n_sides):
    idx = sketch.addGeometry(Part.LineSegment(points[i], points[(i + 1) % n_sides]), False)
    line_ids.append(idx)
doc.recompute()
print(f"added {n_sides} edges: {line_ids}")
```

### Sketch Constraints

```python
# Constrain a closed polygon (Coincident + Equal + Symmetric + Distance)
import FreeCAD, Sketcher
doc = FreeCAD.ActiveDocument
sketch = doc.getObject("Sketch")
# line_ids = list of geometry indices from addGeometry

# Coincident — connect end of each edge to start of next
for i in range(len(line_ids)):
    sketch.addConstraint(Sketcher.Constraint("Coincident",
        line_ids[i], 2, line_ids[(i + 1) % len(line_ids)], 1))

# Equal — all edges same length
for i in range(1, len(line_ids)):
    sketch.addConstraint(Sketcher.Constraint("Equal", line_ids[0], line_ids[i]))

# Symmetric — center on origin (opposite vertices)
sketch.addConstraint(Sketcher.Constraint("Symmetric",
    line_ids[0], 1, line_ids[len(line_ids) // 2], 1, -1, 1))

# Distance — set edge length
sketch.addConstraint(Sketcher.Constraint("Distance", line_ids[0], 20.0))

doc.recompute()
print(f"constraints: {sketch.ConstraintCount}")
```

```python
# Horizontal / Vertical constraints (for rectangular sketches)
import FreeCAD, Sketcher
doc = FreeCAD.ActiveDocument
sketch = doc.getObject("SlotSketch")
# line_id = geometry index
sketch.addConstraint(Sketcher.Constraint("Horizontal", line_id))
sketch.addConstraint(Sketcher.Constraint("Vertical", line_id))
doc.recompute()
```

### Pad and Pocket

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
# Pocket (cut) — attach sketch to a Pad's top face first
import FreeCAD
doc = FreeCAD.ActiveDocument
body = doc.Body
pad = doc.getObject("Pad")
height = pad.Length.Value

# Create sketch and attach to Pad's top face
sketch2 = body.newObject("Sketcher::SketchObject", "SlotSketch")
for i, face in enumerate(pad.Shape.Faces):
    center = face.CenterOfMass
    if abs(center.z - height) < 0.01 and face.Area > 100:  # threshold for main face
        sketch2.AttachmentSupport = [(pad, f"Face{i+1}")]
        sketch2.MapMode = "FlatFace"
        break
doc.recompute()

# ... add geometry and constraints to sketch2 ...

pocket = body.newObject("PartDesign::Pocket", "Pocket")
pocket.Profile = sketch2
pocket.Length = 5.0
doc.recompute()
print(pocket.Name)
```

### Fillet with Edge Selection

```python
# Fillet — select edges by geometric criteria
import FreeCAD, math
doc = FreeCAD.ActiveDocument
body = doc.Body
base_feature = doc.getObject("Pocket")  # last feature in tree
height = 20.0

# Find vertical edges (full-height edges of the solid)
vertical_edges = []
for i, edge in enumerate(base_feature.Shape.Edges):
    vs = edge.Vertexes
    if len(vs) == 2:
        p1, p2 = vs[0].Point, vs[1].Point
        if abs(p1.x - p2.x) < 0.01 and abs(p1.y - p2.y) < 0.01:
            if abs(abs(p1.z - p2.z) - height) < 0.5:
                vertical_edges.append(f"Edge{i+1}")

fillet = body.newObject("PartDesign::Fillet", "SideFillet")
fillet.Base = (base_feature, vertical_edges)
fillet.Radius = 1.0
doc.recompute()
print(f"filleted {len(vertical_edges)} vertical edges")
```

```python
# Fillet — top/bottom edges, excluding a region (e.g. slot)
import FreeCAD, math
doc = FreeCAD.ActiveDocument
base_feature = doc.getObject("SideFillet")
height = 20.0
slot_half_length = 12.5  # half of slot length

top_bottom_edges = []
for i, edge in enumerate(base_feature.Shape.Edges):
    vs = edge.Vertexes
    if len(vs) == 2:
        p1, p2 = vs[0].Point, vs[1].Point
        z_avg = (p1.z + p2.z) / 2
        if abs(z_avg) < 0.01 or abs(z_avg - height) < 0.01:
            # Exclude edges inside the slot region
            mid_x = (p1.x + p2.x) / 2
            mid_y = (p1.y + p2.y) / 2
            mid_r = math.sqrt(mid_x**2 + mid_y**2)
            if mid_r > slot_half_length + 1.0:
                top_bottom_edges.append(f"Edge{i+1}")

fillet2 = doc.Body.newObject("PartDesign::Fillet", "TopBottomFillet")
fillet2.Base = (base_feature, top_bottom_edges)
fillet2.Radius = 2.0
doc.recompute()
print(f"filleted {len(top_bottom_edges)} top/bottom edges")
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

```python
# Save document as FCStd
import FreeCAD, os
doc = FreeCAD.ActiveDocument
save_path = "/tmp/model.FCStd"
os.makedirs(os.path.dirname(save_path), exist_ok=True)
doc.saveAs(save_path)
print(f"saved to {save_path}")
```

## Important Notes

### `doc.recompute()` Timing

Always call `doc.recompute()` after modifying objects. Missing this is the most common cause of stale or incorrect geometry. Call it:
- After adding/modifying sketch geometry or constraints
- After creating Pad, Pocket, Fillet, or any PartDesign feature
- Before reading `Shape` properties (e.g., edge enumeration, face centers)

### Edge/Face Renumbering After Boolean Operations

Edge and Face indices (`Edge1`, `Face3`, etc.) change after boolean operations like Pocket or Fillet. Always re-enumerate edges by iterating `feature.Shape.Edges` with coordinate-based filtering — never hardcode edge numbers across features.

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

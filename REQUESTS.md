## Review

-updating display visualization when changing settings make the UI, some lists of checkboxes and properties to flick

### future suggestion technical improvements?

Use
gc = wx.GraphicsContext.Create(dc)
gc.DrawBitmap(bitmap, x, y, new_w, new_h)
del gc

instead of :
dc.DrawBitmap(bitmap, x, y, True)

for better macOS linux compatibility.
do not recreate GraphicsContext for every tiny element if you can avoid it. Create it once per paint event

- Is that need to be done only in background painting? or for everything?

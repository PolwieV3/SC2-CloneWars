import bpy,json
from pathlib import Path
w=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let/work/atte/video-review');w.mkdir(exist_ok=True)
report=[]
for clip in ['2026-10-24 18-01-12','2026-10-24 18-02-10']:
 bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.render.image_settings.file_format='PNG';s.render.resolution_percentage=50;s.render.use_sequencer=True
 ed=s.sequence_editor_create();strip=ed.strips.new_movie(clip,'B:/Unedited Clips/'+clip+'.mp4',channel=1,frame_start=1)
 s.render.resolution_x=strip.elements[0].orig_width;s.render.resolution_y=strip.elements[0].orig_height
 duration=strip.frame_duration;fps=strip.fps;s.render.fps=round(fps);s.frame_end=duration
 report.append({'clip':clip,'frames':duration,'fps':fps,'duration_seconds':duration/fps})
 for i in range(8):
  frame=1+round((duration-2)*i/7);s.frame_set(frame);s.render.filepath=str(w/(clip+'-'+str(i)+'.png'));bpy.ops.render.render(write_still=True)
(w/'clips.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(report)

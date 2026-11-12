"""PURPOSE: Record the existing input route with loaded native-family identities.
CALLED BY: python run.py --output-dir NEW_DIR under dummy SDL after reviewed installations.
HOW TO MODIFY: Keep the original route unmodified, temporary saves, and honest fixture scope.
"""
import argparse,hashlib,json
from pathlib import Path
from video_game.engine import config
from video_game.engine.room_art_contracts import OPAQUE_BACKDROP_FAMILIES,backdrop_manifest_template
from video_game.engine.scenes.field import FieldOpsScene
from video_game.engine.scenes.bunker import BunkerHubScene
from video_game.tools.mechanics_route import run_route


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
    identities=[];original_field=FieldOpsScene.load_room;original_bunker=BunkerHubScene.on_enter
    def field_enter(scene,*a,**kw):
        result=original_field(scene,*a,**kw)
        family=next((f for f in OPAQUE_BACKDROP_FAMILIES if backdrop_manifest_template(f)['room_id']==scene.room.room_id),None)
        record={'room_id':scene.room.room_id,'family':family,'opaque_loaded':scene.native_opaque is not None,'outdoor_loaded':scene.native_approach is not None}
        if family:
            path=Path(config.ASSETS_DIR)/'environments'/family/'manifest.json'
            record['manifest_sha256']=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        identities.append(record)
        return result
    def bunker_enter(scene,*a,**kw):
        result=original_bunker(scene,*a,**kw);identities.append({'room_id':'bunker_hub','family':'ohio_bunker_v1','opaque_loaded':scene.native_backdrop is not None});return result
    FieldOpsScene.load_room=field_enter;BunkerHubScene.on_enter=bunker_enter
    try:
        result=run_route(args.output_dir)
    finally:
        FieldOpsScene.load_room=original_field;BunkerHubScene.on_enter=original_bunker
    required={'bunker_hub','act_01_mandela_test','act_04_dodleston_relay','flashback_ehman_1977'}
    observed={r['room_id'] for r in identities if r['opaque_loaded']}
    if not required.issubset(observed):raise AssertionError(f'missing native route rooms: {sorted(required-observed)}')
    (args.output_dir/'native_family_identities.json').write_text(json.dumps(identities,indent=2)+'\n')
    (args.output_dir/'mechanics_route.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'native_rooms':sorted(observed),'entries':len(identities),'route_result':result},indent=2))
if __name__=='__main__':main()

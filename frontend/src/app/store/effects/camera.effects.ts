import { Injectable } from "@angular/core";
import { All, AppActionTypes } from "@app/store/actions/app.actions";
import { LoadCameraSuccess } from "@app/store/actions/camera.actions";
import { selectCamera } from "@app/store/selectors/app/camera.selectors";
import { State } from "@app/store/state";
import { Actions, Effect, ofType } from "@ngrx/effects";
import { Store } from "@ngrx/store";
import { CameraApiService } from "@shared/services/api/classic/gear/camera/camera-api.service";
import { EMPTY, Observable, of } from "rxjs";
import { catchError, map, mergeMap } from "rxjs/operators";

@Injectable()
export class CameraEffects {
  @Effect()
  LoadCamera: Observable<LoadCameraSuccess> = this.actions$.pipe(
    ofType(AppActionTypes.LOAD_CAMERA),
    mergeMap(action =>
      this.store$.select(selectCamera, action.payload).pipe(
        mergeMap(cameraFromStore =>
          cameraFromStore !== null
            ? of(cameraFromStore).pipe(map(camera => new LoadCameraSuccess(camera)))
            : this.cameraApiService.getCamera(action.payload).pipe(
                map(camera => new LoadCameraSuccess(camera)),
                catchError(error => EMPTY)
              )
        )
      )
    )
  );

  @Effect({ dispatch: false })
  LoadCameraSuccess: Observable<void> = this.actions$.pipe(ofType(AppActionTypes.LOAD_CAMERA_SUCCESS));

  constructor(
    public readonly store$: Store<State>,
    public readonly actions$: Actions<All>,
    public readonly cameraApiService: CameraApiService
  ) {}
}

import { Injectable } from "@angular/core";
import { All, AppActionTypes } from "@app/store/actions/app.actions";
import { LoadImagesSuccess, LoadImageSuccess } from "@app/store/actions/image.actions";
import { selectImage } from "@app/store/selectors/app/image.selectors";
import { State } from "@app/store/state";
import { Actions, Effect, ofType } from "@ngrx/effects";
import { Store } from "@ngrx/store";
import { ImageApiService } from "@shared/services/api/classic/images/image/image-api.service";
import { EMPTY, Observable, of } from "rxjs";
import { catchError, map, mergeMap } from "rxjs/operators";

@Injectable()
export class ImageEffects {
  @Effect()
  LoadImage: Observable<LoadImageSuccess> = this.actions$.pipe(
    ofType(AppActionTypes.LOAD_IMAGE),
    mergeMap(action =>
      this.store$.select(selectImage, action.payload).pipe(
        mergeMap(imageFromStore =>
          imageFromStore !== null
            ? of(imageFromStore).pipe(map(image => new LoadImageSuccess(image)))
            : this.imageApiService.getImage(action.payload).pipe(
                map(image => new LoadImageSuccess(image)),
                catchError(error => EMPTY)
              )
        )
      )
    )
  );

  @Effect({ dispatch: false })
  LoadImageSuccess: Observable<void> = this.actions$.pipe(ofType(AppActionTypes.LOAD_IMAGE_SUCCESS));

  @Effect()
  LoadImages: Observable<LoadImagesSuccess> = this.actions$.pipe(
    ofType(AppActionTypes.LOAD_IMAGES),
    mergeMap(action =>
      this.imageApiService.getImages(action.payload).pipe(
        map(response => new LoadImagesSuccess(response)),
        catchError(error => EMPTY)
      )
    )
  );

  @Effect({ dispatch: false })
  LoadImagesSuccess: Observable<void> = this.actions$.pipe(ofType(AppActionTypes.LOAD_IMAGES_SUCCESS));

  constructor(
    public readonly store$: Store<State>,
    public readonly actions$: Actions<All>,
    public readonly imageApiService: ImageApiService
  ) {}
}

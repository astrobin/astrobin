import { Injectable } from "@angular/core";
import { All, AppActionTypes } from "@app/store/actions/app.actions";
import { LoadContentTypeSuccess } from "@app/store/actions/content-type.actions";
import { selectContentType } from "@app/store/selectors/app/content-type.selectors";
import { State } from "@app/store/state";
import { Actions, Effect, ofType } from "@ngrx/effects";
import { Store } from "@ngrx/store";
import { CommonApiService } from "@shared/services/api/classic/common/common-api.service";
import { EMPTY, Observable, of } from "rxjs";
import { catchError, map, mergeMap } from "rxjs/operators";

@Injectable()
export class ContentTypeEffects {
  @Effect()
  LoadCamera: Observable<LoadContentTypeSuccess> = this.actions$.pipe(
    ofType(AppActionTypes.LOAD_CONTENT_TYPE),
    mergeMap(action =>
      this.store$.select(selectContentType, action.payload).pipe(
        mergeMap(fromStore =>
          fromStore !== null
            ? of(fromStore).pipe(map(contentType => new LoadContentTypeSuccess(contentType)))
            : this.commonApiService.getContentType(action.payload.appLabel, action.payload.model).pipe(
                map(contentType => new LoadContentTypeSuccess(contentType)),
                catchError(error => EMPTY)
              )
        )
      )
    )
  );

  @Effect({ dispatch: false })
  LoadContentTypeSuccess: Observable<void> = this.actions$.pipe(ofType(AppActionTypes.LOAD_CONTENT_TYPE_SUCCESS));

  constructor(
    public readonly store$: Store<State>,
    public readonly actions$: Actions<All>,
    public readonly commonApiService: CommonApiService
  ) {}
}

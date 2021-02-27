import { Injectable } from "@angular/core";
import { All, AppActionTypes } from "@app/store/actions/app.actions";
import { HideFullscreenImage, ShowFullscreenImage } from "@app/store/actions/fullscreen-image.actions";
import { State } from "@app/store/state";
import { Actions, Effect, ofType } from "@ngrx/effects";
import { Store } from "@ngrx/store";
import { WindowRefService } from "@shared/services/window-ref.service";
import { Observable } from "rxjs";

@Injectable()
export class FullscreenImageEffects {
  @Effect({ dispatch: false })
  showFullscreenImage$: Observable<ShowFullscreenImage> = this.actions$.pipe(
    ofType(AppActionTypes.SHOW_FULLSCREEN_IMAGE)
  );

  @Effect({ dispatch: false })
  hideFullscreenImage$: Observable<HideFullscreenImage> = this.actions$.pipe(
    ofType(AppActionTypes.HIDE_FULLSCREEN_IMAGE)
  );

  constructor(
    public readonly store$: Store<State>,
    public readonly actions$: Actions<All>,
    public readonly windowRef: WindowRefService
  ) {}
}

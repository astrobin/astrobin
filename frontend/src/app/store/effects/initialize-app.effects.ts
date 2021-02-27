import { Injectable } from "@angular/core";
import { All, AppActionTypes } from "@app/store/actions/app.actions";
import { InitializeAppSuccess } from "@app/store/actions/initialize-app.actions";
import { setTimeagoIntl } from "@app/translate-loader";
import { Actions, Effect, ofType } from "@ngrx/effects";
import { TranslateService } from "@ngx-translate/core";
import { CommonApiService } from "@shared/services/api/classic/common/common-api.service";
import { JsonApiService } from "@shared/services/api/classic/json/json-api.service";
import { WindowRefService } from "@shared/services/window-ref.service";
import { TimeagoIntl } from "ngx-timeago";
import { forkJoin, Observable, of } from "rxjs";
import { map, switchMap } from "rxjs/operators";

@Injectable()
export class InitializeAppEffects {
  @Effect()
  InitializeApp: Observable<InitializeAppSuccess> = this.actions$.pipe(
    ofType(AppActionTypes.INITIALIZE),
    switchMap(() => {
      // @ts-ignore
      let language = this.windowRef.nativeWindow.navigator.language || "en";
      if (language.indexOf("-") > -1) {
        language = language.split("-")[0];
      }

      const subscriptions$ = this.commonApiService.getSubscriptions();
      const language$ = of(language);
      const backendConfig$ = this.jsonApiService.getBackendConfig();

      return forkJoin([language$, subscriptions$, backendConfig$, this.translate.use(language)]).pipe(
        map(results => {
          this.translate.setDefaultLang(language);
          setTimeagoIntl(this.timeagoIntl, language);
          return new InitializeAppSuccess({
            language: results[0],
            subscriptions: results[1],
            backendConfig: results[2]
          });
        })
      );
    })
  );

  @Effect({ dispatch: false })
  InitializeAppSuccess: Observable<void> = this.actions$.pipe(ofType(AppActionTypes.INITIALIZE_SUCCESS));

  constructor(
    public readonly actions$: Actions<All>,
    public readonly commonApiService: CommonApiService,
    public readonly jsonApiService: JsonApiService,
    public readonly translate: TranslateService,
    public readonly timeagoIntl: TimeagoIntl,
    public readonly windowRef: WindowRefService
  ) {}
}

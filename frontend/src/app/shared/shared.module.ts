import { CommonModule } from "@angular/common";
import { HttpClientModule } from "@angular/common/http";
import { APP_INITIALIZER, ModuleWithProviders, NgModule } from "@angular/core";
import { FormsModule, ReactiveFormsModule } from "@angular/forms";
import { formlyValidationConfig } from "@app/formly.config";
import { AppActionTypes } from "@app/store/actions/app.actions";
import { InitializeApp } from "@app/store/actions/initialize-app.actions";
import { State } from "@app/store/state";
import { AuthActionTypes, InitializeAuth } from "@features/account/store/auth.actions";
import { FontAwesomeModule } from "@fortawesome/angular-fontawesome";
import { NgbModule, NgbPaginationModule, NgbProgressbarModule } from "@ng-bootstrap/ng-bootstrap";
import { NgSelectModule } from "@ng-select/ng-select";
import { Actions, ofType } from "@ngrx/effects";
import { Store } from "@ngrx/store";
import { FormlyBootstrapModule } from "@ngx-formly/bootstrap";
import { FORMLY_CONFIG, FormlyModule } from "@ngx-formly/core";
import { TranslateModule, TranslateService } from "@ngx-translate/core";
import { ApiModule } from "@shared/services/api/api.module";
import { AuthService } from "@shared/services/auth.service";
import { ClassicRoutesService } from "@shared/services/classic-routes.service";
import { AuthGuardService } from "@shared/services/guards/auth-guard.service";
import { GroupGuardService } from "@shared/services/guards/group-guard.service";
import { ImageOwnerGuardService } from "@shared/services/guards/image-owner-guard.service";
import { UltimateSubscriptionGuardService } from "@shared/services/guards/ultimate-subscription-guard.service";
import { LoadingService } from "@shared/services/loading.service";
import { PopNotificationsService } from "@shared/services/pop-notifications.service";
import { SessionService } from "@shared/services/session.service";
import { UserStoreService } from "@shared/services/user-store.service";
import { UserService } from "@shared/services/user.service";
import { WindowRefService } from "@shared/services/window-ref.service";
import { StickyNavModule } from "ng2-sticky-nav";
import { CookieService } from "ngx-cookie-service";
import { NgxFilesizeModule } from "ngx-filesize";
import { TimeagoModule } from "ngx-timeago";
import { ToastrModule } from "ngx-toastr";
import { switchMap } from "rxjs/operators";
import { ComponentsModule } from "./components/components.module";
import { PipesModule } from "./pipes/pipes.module";

export function appInitializer(store: Store<State>, actions$: Actions) {
  return () =>
    new Promise<any>(resolve => {
      store.dispatch(new InitializeApp());

      actions$
        .pipe(
          ofType(AppActionTypes.INITIALIZE_SUCCESS),
          switchMap(() => {
            store.dispatch(new InitializeAuth());
            return actions$.pipe(ofType(AuthActionTypes.INITIALIZE_SUCCESS));
          })
        )
        .subscribe(() => {
          resolve();
        });
    });
}

@NgModule({
  imports: [
    CommonModule,
    ComponentsModule,
    HttpClientModule,
    FormsModule,
    ReactiveFormsModule,

    FontAwesomeModule,
    FormlyModule.forRoot(),
    FormlyBootstrapModule,
    NgbModule,
    NgbPaginationModule,
    NgbProgressbarModule,
    NgSelectModule,
    NgxFilesizeModule,
    ToastrModule.forRoot({
      timeOut: 20000,
      progressBar: true,
      preventDuplicates: true,
      resetTimeoutOnDuplicate: true
    }),
    StickyNavModule,

    ApiModule,
    PipesModule
  ],
  exports: [
    CommonModule,
    ComponentsModule,
    HttpClientModule,
    FormsModule,
    ReactiveFormsModule,

    FontAwesomeModule,
    FormlyModule,
    FormlyBootstrapModule,
    NgbModule,
    NgbPaginationModule,
    NgbProgressbarModule,
    NgSelectModule,
    NgxFilesizeModule,
    ToastrModule,
    TimeagoModule,
    TranslateModule,
    StickyNavModule,

    ApiModule,
    PipesModule
  ]
})
export class SharedModule {
  static forRoot(): ModuleWithProviders<SharedModule> {
    return {
      ngModule: SharedModule,
      providers: [
        AuthGuardService,
        AuthService,
        ClassicRoutesService,
        CookieService,
        GroupGuardService,
        ImageOwnerGuardService,
        LoadingService,
        PopNotificationsService,
        SessionService,
        UltimateSubscriptionGuardService,
        UserService,
        UserStoreService,
        WindowRefService,
        {
          provide: APP_INITIALIZER,
          useFactory: appInitializer,
          multi: true,
          deps: [Store, Actions]
        },
        {
          provide: FORMLY_CONFIG,
          useFactory: formlyValidationConfig,
          multi: true,
          deps: [TranslateService]
        }
      ]
    };
  }
}

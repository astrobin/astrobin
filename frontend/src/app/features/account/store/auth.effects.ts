import { Injectable } from "@angular/core";
import { Router } from "@angular/router";
import { setTimeagoIntl } from "@app/translate-loader";
import {
  AuthActionTypes,
  InitializeAuthSuccess,
  Login,
  LoginFailure,
  LoginSuccess
} from "@features/account/store/auth.actions";
import { LoginSuccessInterface } from "@features/account/store/auth.actions.interfaces";
import { Actions, Effect, ofType } from "@ngrx/effects";
import { TranslateService } from "@ngx-translate/core";
import { UserProfileInterface } from "@shared/interfaces/user-profile.interface";
import { UserSubscriptionInterface } from "@shared/interfaces/user-subscription.interface";
import { UserInterface } from "@shared/interfaces/user.interface";
import { CommonApiService } from "@shared/services/api/classic/common/common-api.service";
import { AuthService } from "@shared/services/auth.service";
import { LoadingService } from "@shared/services/loading.service";
import { UserStoreService } from "@shared/services/user-store.service";
import { CookieService } from "ngx-cookie-service";
import { TimeagoIntl } from "ngx-timeago";
import { forkJoin, Observable, of } from "rxjs";
import { catchError, map, switchMap, tap } from "rxjs/operators";

@Injectable()
export class AuthEffects {
  @Effect()
  Initialize: Observable<InitializeAuthSuccess> = this.actions$.pipe(
    ofType(AuthActionTypes.INITIALIZE),
    switchMap(() =>
      new Observable<LoginSuccessInterface>(observer => {
        if (this.cookieService.check(AuthService.CLASSIC_AUTH_TOKEN_COOKIE)) {
          this._getData$.subscribe(data => {
            const successPayload: LoginSuccessInterface = {
              user: data.user,
              userProfile: data.userProfile,
              userSubscriptions: data.userSubscriptions
            };

            observer.next(successPayload);
            observer.complete();
          });
        } else {
          observer.next({ user: null, userProfile: null, userSubscriptions: [] });
          observer.complete();
        }
      }).pipe(map(payload => new InitializeAuthSuccess(payload)))
    )
  );

  @Effect({ dispatch: false })
  InitializeSuccess: Observable<InitializeAuthSuccess> = this.actions$.pipe(
    ofType(AuthActionTypes.INITIALIZE_SUCCESS),
    tap(action => {
      if (action.payload.user && action.payload.userProfile) {
        this.userStore.addUserProfile(action.payload.userProfile);
        this.userStore.addUser(action.payload.user);
      }
    })
  );

  @Effect()
  Login: Observable<LoginSuccess | LoginFailure> = this.actions$.pipe(
    ofType(AuthActionTypes.LOGIN),
    map((action: Login) => action),
    tap(action => {
      this.loadingService.setLoading(true);
      return action;
    }),
    switchMap(action =>
      this.authService.login(action.payload.handle, action.payload.password, action.payload.redirectUrl).pipe(
        tap(token => {
          this.cookieService.set(AuthService.CLASSIC_AUTH_TOKEN_COOKIE, token, 180, "/");
        }),
        switchMap(() =>
          this._getData$.pipe(
            map(data => ({
              user: data.user,
              userProfile: data.userProfile,
              userSubscriptions: data.userSubscriptions,
              redirectUrl: action.payload.redirectUrl
            }))
          )
        ),
        map(payload => new LoginSuccess(payload)),
        catchError(error => of(new LoginFailure({ error })))
      )
    )
  );

  @Effect({ dispatch: false })
  LoginSuccess: Observable<LoginSuccess> = this.actions$.pipe(
    ofType(AuthActionTypes.LOGIN_SUCCESS),
    tap(action => {
      this.userStore.addUserProfile(action.payload.userProfile);
      this.userStore.addUser(action.payload.user);

      this.loadingService.setLoading(false);

      this.router.navigate(["account", "logged-in"], { queryParams: { redirectUrl: action.payload.redirectUrl } });
    })
  );

  @Effect({ dispatch: false })
  LoginFailure: Observable<void> = this.actions$.pipe(
    ofType(AuthActionTypes.LOGIN_FAILURE),
    tap(() => {
      this.loadingService.setLoading(false);
    })
  );

  @Effect({ dispatch: false })
  Logout: Observable<void> = this.actions$.pipe(
    ofType(AuthActionTypes.LOGOUT),
    tap(() => {
      if (this.cookieService.check(AuthService.CLASSIC_AUTH_TOKEN_COOKIE)) {
        this.cookieService.delete(AuthService.CLASSIC_AUTH_TOKEN_COOKIE, "/");
        this.router.navigate(["account", "logged-out"]);
      }
    })
  );

  private _getCurrentUserProfile$: Observable<UserProfileInterface> = this.commonApiService.getCurrentUserProfile();

  private _getCurrentUser$: Observable<UserInterface> = this._getCurrentUserProfile$.pipe(
    switchMap(userProfile => {
      if (userProfile !== null) {
        return this.commonApiService.getUser(userProfile.user);
      }

      return of(null);
    })
  );

  private _getUserSubscriptions$: Observable<UserSubscriptionInterface[]> = this._getCurrentUser$.pipe(
    switchMap(user => {
      if (user !== null) {
        return this.commonApiService.getUserSubscriptions(user);
      }

      return of(null);
    })
  );

  private _getData$ = forkJoin({
    user: this._getCurrentUser$,
    userProfile: this._getCurrentUserProfile$,
    userSubscriptions: this._getUserSubscriptions$
  }).pipe(
    switchMap(data => forkJoin([of(data), this._setLanguage(data.userProfile.language)])),
    map(result => result[0])
  );

  private _setLanguage(language: string): Observable<any> {
    this.translate.setDefaultLang(language);
    return this.translate.use(language).pipe(
      map(() => {
        setTimeagoIntl(this.timeagoIntl, language);
      })
    );
  }

  constructor(
    public readonly actions$: Actions,
    public readonly authService: AuthService,
    public readonly router: Router,
    public readonly cookieService: CookieService,
    public readonly loadingService: LoadingService,
    public readonly commonApiService: CommonApiService,
    public readonly userStore: UserStoreService,
    public readonly translate: TranslateService,
    public readonly timeagoIntl: TimeagoIntl
  ) {}
}

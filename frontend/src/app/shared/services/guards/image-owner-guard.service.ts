import { Location } from "@angular/common";
import { Injectable } from "@angular/core";
import { ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot } from "@angular/router";
import { State } from "@app/store/state";
import { Store } from "@ngrx/store";
import { ImageApiService } from "@shared/services/api/classic/images/image/image-api.service";
import { BaseService } from "@shared/services/base.service";
import { LoadingService } from "@shared/services/loading.service";
import { EMPTY, Observable, Observer } from "rxjs";
import { catchError, map, switchMap } from "rxjs/operators";
import { AuthService } from "../auth.service";

@Injectable()
export class ImageOwnerGuardService extends BaseService implements CanActivate {
  constructor(
    public readonly store: Store<State>,
    public loadingService: LoadingService,
    public authService: AuthService,
    public imageApiService: ImageApiService,
    public router: Router,
    public location: Location
  ) {
    super(loadingService);
  }

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<boolean> {
    const onSuccess = (observer: Observer<boolean>) => {
      observer.next(true);
      observer.complete();
    };

    const onError = (observer: Observer<boolean>, redirectTo: string) => {
      this.router.navigateByUrl(redirectTo, { skipLocationChange: true }).then(() => {
        observer.next(false);
        observer.complete();
        this.location.replaceState(state.url);
      });
    };

    return new Observable<boolean>(observer => {
      this.authService.isAuthenticated().subscribe(authenticated => {
        if (!authenticated) {
          observer.next(false);
          observer.complete();
          return;
        }

        this.store
          .pipe(
            switchMap(storeState =>
              this.imageApiService.getImage(+route.params["imageId"]).pipe(map(image => ({ storeState, image })))
            ),
            catchError(err => {
              onError(observer, "/404");
              return EMPTY;
            }),
            map(({ storeState, image }) => image.user === storeState.auth.user.id)
          )
          .subscribe(canActivate => {
            if (canActivate) {
              onSuccess(observer);
            } else {
              onError(observer, "/permission-denied");
            }
          });
      });
    });
  }
}

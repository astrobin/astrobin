import { Location } from "@angular/common";
import { Injectable } from "@angular/core";
import { ActivatedRouteSnapshot, Resolve, Router, RouterStateSnapshot } from "@angular/router";
import { LoadImage } from "@app/store/actions/image.actions";
import { selectImage } from "@app/store/selectors/app/image.selectors";
import { State } from "@app/store/state";
import { Store } from "@ngrx/store";
import { ImageApiService } from "@shared/services/api/classic/images/image/image-api.service";
import { EMPTY, Observable } from "rxjs";
import { catchError, filter, take } from "rxjs/operators";
import { ImageInterface } from "../interfaces/image.interface";

@Injectable({
  providedIn: "root"
})
export class ImageResolver implements Resolve<ImageInterface> {
  constructor(
    private service: ImageApiService,
    private router: Router,
    private location: Location,
    private store$: Store<State>
  ) {}

  resolve(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<any> | Promise<any> | any {
    const id = route.paramMap.get("imageId");

    this.store$.dispatch(new LoadImage(id));

    return this.store$.select(selectImage, id).pipe(
      filter(image => !!image),
      take(1),
      catchError(err => {
        this.router.navigateByUrl("/404", { skipLocationChange: true }).then(() => {
          this.location.replaceState(state.url);
        });
        return EMPTY;
      })
    );
  }
}

import { Location } from "@angular/common";
import { Injectable } from "@angular/core";
import { ActivatedRouteSnapshot, Resolve, Router, RouterStateSnapshot } from "@angular/router";
import { ImageApiService } from "@shared/services/api/classic/images/image/image-api.service";
import { EMPTY, Observable } from "rxjs";
import { catchError } from "rxjs/operators";
import { ImageInterface } from "../interfaces/image.interface";

@Injectable({
  providedIn: "root"
})
export class ImageResolver implements Resolve<ImageInterface> {
  constructor(private service: ImageApiService, private router: Router, private location: Location) {}

  resolve(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<any> | Promise<any> | any {
    return this.service.getImage(+route.paramMap.get("imageId")).pipe(
      catchError(err => {
        this.router.navigateByUrl("/404", { skipLocationChange: true }).then(() => {
          this.location.replaceState(state.url);
        });
        return EMPTY;
      })
    );
  }
}

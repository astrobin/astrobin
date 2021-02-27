import { Component, OnInit } from "@angular/core";
import { selectBreadcrumb } from "@app/store/selectors/app/app.selectors";
import { State } from "@app/store/state";
import { Store } from "@ngrx/store";
import { BaseComponentDirective } from "@shared/components/base-component.directive";
import { BreadcrumbInterface } from "@shared/components/misc/breadcrumb/breadcrumb.interface";
import { ClassicRoutesService } from "@shared/services/classic-routes.service";
import { Observable } from "rxjs";
import { takeUntil } from "rxjs/operators";

@Component({
  selector: "astrobin-breadcrumb",
  templateUrl: "./breadcrumb.component.html",
  styleUrls: ["./breadcrumb.component.scss"]
})
export class BreadcrumbComponent extends BaseComponentDirective implements OnInit {
  breadcrumb$: Observable<BreadcrumbInterface[]>;

  constructor(public readonly store$: Store<State>, public readonly classicRoutesService: ClassicRoutesService) {
    super();
  }

  ngOnInit(): void {
    this.breadcrumb$ = this.store$.select(selectBreadcrumb).pipe(takeUntil(this.destroyed$));
  }
}

import { Component, OnInit } from "@angular/core";
import { SetBreadcrumb } from "@app/store/actions/breadcrumb.actions";
import { State } from "@app/store/state";
import { Store } from "@ngrx/store";
import { TranslateService } from "@ngx-translate/core";
import { ClassicRoutesService } from "@shared/services/classic-routes.service";
import { TitleService } from "@shared/services/title/title.service";

@Component({
  selector: "astrobin-permission-denied-page",
  templateUrl: "./permission-denied-page.component.html"
})
export class PermissionDeniedPageComponent implements OnInit {
  constructor(
    public readonly store$: Store<State>,
    public readonly classicRoutes: ClassicRoutesService,
    public readonly translateService: TranslateService,
    public readonly titleService: TitleService
  ) {}

  ngOnInit(): void {
    const title = this.translateService.instant("Permission denied");
    this.titleService.setTitle(title);
    this.store$.dispatch(
      new SetBreadcrumb({
        breadcrumb: [{ label: title }]
      })
    );
  }
}

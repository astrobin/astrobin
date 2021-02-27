import { Component, OnInit } from "@angular/core";
import { SetBreadcrumb } from "@app/store/actions/breadcrumb.actions";
import { State } from "@app/store/state";
import { Store } from "@ngrx/store";
import { TranslateService } from "@ngx-translate/core";
import { BaseComponentDirective } from "@shared/components/base-component.directive";
import { TitleService } from "@shared/services/title/title.service";

@Component({
  selector: "astrobin-not-found-page",
  templateUrl: "./not-found-404-page.component.html"
})
export class NotFound404PageComponent extends BaseComponentDirective implements OnInit {
  constructor(
    public readonly store$: Store<State>,
    public readonly titleService: TitleService,
    public readonly translateService: TranslateService
  ) {
    super();
  }

  ngOnInit() {
    const title = "404";
    this.titleService.setTitle(title);

    this.store$.dispatch(
      new SetBreadcrumb({
        breadcrumb: [{ label: title }]
      })
    );
  }
}

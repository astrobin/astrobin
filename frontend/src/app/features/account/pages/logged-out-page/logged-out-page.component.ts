import { Component, OnInit } from "@angular/core";
import { SetBreadcrumb } from "@app/store/actions/breadcrumb.actions";
import { State } from "@app/store/state";
import { Store } from "@ngrx/store";
import { TranslateService } from "@ngx-translate/core";
import { BaseComponentDirective } from "@shared/components/base-component.directive";
import { TitleService } from "@shared/services/title/title.service";

@Component({
  selector: "astrobin-logged-out-page",
  templateUrl: "./logged-out-page.component.html"
})
export class LoggedOutPageComponent extends BaseComponentDirective implements OnInit {
  constructor(
    public readonly store$: Store<State>,
    public readonly titleService: TitleService,
    public readonly translate: TranslateService
  ) {
    super();
  }

  ngOnInit() {
    const title = this.translate.instant("Good bye!");
    this.titleService.setTitle(title);
    this.store$.dispatch(new SetBreadcrumb({ breadcrumb: [{ label: "Account" }, { label: title }] }));
  }
}

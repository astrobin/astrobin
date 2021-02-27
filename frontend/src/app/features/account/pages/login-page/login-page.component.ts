import { Component, OnInit, ViewChild } from "@angular/core";
import { ActivatedRoute, Router } from "@angular/router";
import { SetBreadcrumb } from "@app/store/actions/breadcrumb.actions";
import { State } from "@app/store/state";
import { Store } from "@ngrx/store";
import { TranslateService } from "@ngx-translate/core";
import { LoginFormComponent } from "@shared/components/auth/login-form/login-form.component";
import { BaseComponentDirective } from "@shared/components/base-component.directive";
import { ClassicRoutesService } from "@shared/services/classic-routes.service";
import { LoadingService } from "@shared/services/loading.service";
import { TitleService } from "@shared/services/title/title.service";

@Component({
  selector: "astrobin-login-page",
  templateUrl: "./login-page.component.html",
  styleUrls: ["./login-page.component.scss"]
})
export class LoginPageComponent extends BaseComponentDirective implements OnInit {
  redirectUrl: string;

  @ViewChild("loginForm") loginForm: LoginFormComponent;

  constructor(
    public readonly store$: Store<State>,
    public readonly classicRoutesService: ClassicRoutesService,
    public readonly route: ActivatedRoute,
    public readonly translate: TranslateService,
    public readonly titleService: TitleService,
    public readonly loadingService: LoadingService
  ) {
    super();
  }

  ngOnInit(): void {
    const title = this.translate.instant("Log in");
    this.titleService.setTitle(title);
    this.store$.dispatch(new SetBreadcrumb({ breadcrumb: [{ label: "Account" }, { label: title }] }));
    this.redirectUrl = this.route.snapshot.queryParamMap.get("redirectUrl");
  }
}

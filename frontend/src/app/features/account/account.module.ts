import { NgModule } from "@angular/core";
import { RouterModule } from "@angular/router";
import { routes } from "@features/account/account.routing";
import { LoggedInPageComponent } from "@features/account/pages/logged-in-page/logged-in-page.component";
import { SharedModule } from "@shared/shared.module";
import { LoggedOutPageComponent } from "./pages/logged-out-page/logged-out-page.component";
import { LoginPageComponent } from "./pages/login-page/login-page.component";

@NgModule({
  declarations: [LoginPageComponent, LoggedInPageComponent, LoggedOutPageComponent],
  imports: [RouterModule.forChild(routes), SharedModule]
})
export class AccountModule {}

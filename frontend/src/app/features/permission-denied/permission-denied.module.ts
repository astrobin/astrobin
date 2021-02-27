import { NgModule } from "@angular/core";
import { RouterModule } from "@angular/router";
import { routes } from "@features/permission-denied/permission-denied.routing";
import { SharedModule } from "@shared/shared.module";
import { PermissionDeniedPageComponent } from "./pages/permission-denied-page/permission-denied-page.component";

@NgModule({
  declarations: [PermissionDeniedPageComponent],
  imports: [RouterModule.forChild(routes), SharedModule]
})
export class PermissionDeniedModule {}

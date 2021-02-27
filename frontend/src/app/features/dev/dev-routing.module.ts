import { NgModule } from "@angular/core";
import { RouterModule, Routes } from "@angular/router";
import { ImageTestPageComponent } from "@features/dev/image-test-page/image-test-page.component";

const routes: Routes = [
  {
    path: "image",
    component: ImageTestPageComponent
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class DevRoutingModule {}

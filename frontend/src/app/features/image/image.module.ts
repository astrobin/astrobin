import { NgModule } from "@angular/core";
import { RouterModule } from "@angular/router";
import { FormlyFieldImageEditStepperComponent } from "@features/image/components/formly-field-image-edit-stepper/formly-field-image-edit-stepper.component";
import { routes } from "@features/image/image.routing";
import { SharedModule } from "@shared/shared.module";
import { ImageEditPageComponent } from "./pages/edit/image-edit-page.component";

@NgModule({
  declarations: [FormlyFieldImageEditStepperComponent, ImageEditPageComponent],
  imports: [RouterModule.forChild(routes), SharedModule]
})
export class ImageModule {}

import { CommonModule } from "@angular/common";
import { NgModule } from "@angular/core";
import { FormsModule, ReactiveFormsModule } from "@angular/forms";
import { RouterModule } from "@angular/router";
import { formlyValidationConfig } from "@app/formly.config";
import { ObjectsInFieldComponent } from "@app/shared/components/misc/objects-in-field/objects-in-field.component";
import { FontAwesomeModule } from "@fortawesome/angular-fontawesome";
import {
  NgbCollapseModule,
  NgbDropdownModule,
  NgbModalModule,
  NgbProgressbarModule,
  NgbTooltipModule
} from "@ng-bootstrap/ng-bootstrap";
import { FORMLY_CONFIG, FormlyModule } from "@ngx-formly/core";
import { TranslateModule, TranslateService } from "@ngx-translate/core";
import { BreadcrumbComponent } from "@shared/components/misc/breadcrumb/breadcrumb.component";
import { CameraComponent } from "@shared/components/misc/camera/camera.component";
import { FormlyFieldChunkedFileAccessorDirective } from "@shared/components/misc/formly-field-chunked-file/formly-field-chunked-file-accessor.directive";
import { FormlyFieldChunkedFileComponent } from "@shared/components/misc/formly-field-chunked-file/formly-field-chunked-file.component";
import { FullscreenImageViewerComponent } from "@shared/components/misc/fullscreen-image-viewer/fullscreen-image-viewer.component";
import { ImageComponent } from "@shared/components/misc/image/image.component";
import { LoadingIndicatorComponent } from "@shared/components/misc/loading-indicator/loading-indicator.component";
import { RefreshButtonComponent } from "@shared/components/misc/refresh-button/refresh-button.component";
import { TelescopeComponent } from "@shared/components/misc/telescope/telescope.component";
import { TextLoadingIndicatorComponent } from "@shared/components/misc/text-loading-indicator/text-loading-indicator.component";
import { PipesModule } from "@shared/pipes/pipes.module";
import { NgxFilesizeModule } from "ngx-filesize";
import { NgxImageZoomModule } from "ngx-image-zoom";
import { UploadxModule } from "ngx-uploadx";
import { LoginFormComponent } from "./auth/login-form/login-form.component";
import { LoginModalComponent } from "./auth/login-modal/login-modal.component";
import { FooterComponent } from "./footer/footer.component";
import { HeaderComponent } from "./header/header.component";
import { EmptyListComponent } from "./misc/empty-list/empty-list.component";
import { ReadOnlyModeComponent } from "./misc/read-only-mode/read-only-mode.component";
import { UsernameComponent } from "./misc/username/username.component";

const modules = [
  CommonModule,
  FontAwesomeModule,
  FormsModule,
  NgbCollapseModule,
  NgbDropdownModule,
  NgbModalModule,
  NgbProgressbarModule,
  NgbTooltipModule,
  NgxFilesizeModule,
  NgxImageZoomModule,
  PipesModule,
  ReactiveFormsModule,
  RouterModule,
  TranslateModule,
  FormlyModule,
  UploadxModule
];

const components = [
  BreadcrumbComponent,
  CameraComponent,
  EmptyListComponent,
  FooterComponent,
  FormlyFieldChunkedFileAccessorDirective,
  FormlyFieldChunkedFileComponent,
  FullscreenImageViewerComponent,
  HeaderComponent,
  ImageComponent,
  LoadingIndicatorComponent,
  LoginFormComponent,
  LoginModalComponent,
  ObjectsInFieldComponent,
  ReadOnlyModeComponent,
  RefreshButtonComponent,
  TelescopeComponent,
  TextLoadingIndicatorComponent,
  UsernameComponent
];

@NgModule({
  imports: modules,
  declarations: components,
  exports: components,
  providers: [
    {
      provide: FORMLY_CONFIG,
      useFactory: formlyValidationConfig,
      multi: true,
      deps: [TranslateService]
    }
  ]
})
export class ComponentsModule {}

import { UserModel } from "./user.model";
import { UserSubscriptionModel } from "./usersubscription.model";

export class UserProfileModel {
  // Backend fields.
  id: number;
  deleted?: Date;
  updated?: Date;
  real_name?: string;
  website?: string;
  job?: string;
  hobbies?: string;
  timezone?: string;
  about?: string;
  premium_counter: number;
  company_name?: string;
  company_description?: string;
  company_website?: string;
  retailer_country?: string;
  avatar?: string;
  exclude_from_competitions: boolean;
  default_frontpage_section: string;
  default_gallery_sorting: number;
  default_license: number;
  default_watermark_text?: string;
  default_watermark: boolean;
  default_watermark_size: string;
  default_watermark_position: number;
  default_watermark_opacity: number;
  accept_tos: boolean;
  receive_important_communications: boolean;
  receive_newsletter: boolean;
  receive_marketing_and_commercial_material: boolean;
  language?: string;
  seen_realname: boolean;
  seen_email_permissions: boolean;
  signature: string;
  signature_html: string;
  show_signatures: boolean;
  post_count: number;
  autosubscribe: boolean;
  receive_forum_emails: boolean;
  user: number;
  telescopes?: number[];
  mounts?: number[];
  cameras?: number[];
  focal_reducers?: number[];
  software?: number[];
  filters?: number[];
  accessories?: number[];

  // Computed, convenience fields.
  userObject?: UserModel;
  userSubscriptionObjects?: UserSubscriptionModel[];
  hasValidRawDataSubscription?: boolean;

  constructor(values: Object = {}) {
    Object.assign(this, values);
  }
}

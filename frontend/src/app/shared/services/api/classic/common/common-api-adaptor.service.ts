import { Injectable } from "@angular/core";
import { GroupInterface } from "@shared/interfaces/group.interface";
import { PermissionInterface } from "@shared/interfaces/permission.interface";
import { UserProfileInterface } from "@shared/interfaces/user-profile.interface";
import { UserInterface } from "@shared/interfaces/user.interface";
import { BaseService } from "@shared/services/base.service";

export interface BackendPermissionInterface {
  id: number;
  name: string;
  codename: string;
  content_type: number;
}

export interface BackendGroupInterface {
  id: number;
  name: string;
  permissions: BackendPermissionInterface[];
}

export interface BackendUserInterface {
  id: number;
  avatar: string;
  userprofile: number;
  last_login: string;
  is_superuser: boolean;
  username: string;
  first_name: string;
  is_staff: boolean;
  is_active: boolean;
  date_joined: string;
  groups: BackendGroupInterface[];
  user_permissions: BackendPermissionInterface[];
}

export interface BackendUserProfileInterface {
  id: number;
  deleted: string;
  updated: string;
  real_name: string;
  website: string;
  job: string;
  hobbies: string;
  timezone: string;
  about: string;
  company_name: string;
  company_description: string;
  company_website: string;
  retailer_country: string;
  avatar: string;
  exclude_from_competitions: boolean;
  default_frontpage_section: string;
  default_gallery_sorting: number;
  default_license: number;
  default_watermark_text: string;
  default_watermark: boolean;
  default_watermark_size: string;
  default_watermark_position: number;
  default_watermark_opacity: number;
  accept_tos: boolean;
  receive_important_communications: boolean;
  receive_newsletter: boolean;
  receive_marketing_and_commercial_material: boolean;
  language: string;
  seen_realname: boolean;
  seen_email_permissions: boolean;
  signature: string;
  signature_html: string;
  show_signatures: boolean;
  post_count: number;
  autosubscribe: boolean;
  receive_forum_emails: boolean;
  user: number;
  telescopes: number[];
  mounts: number[];
  cameras: number[];
  focal_reducers: number[];
  software: number[];
  filters: number[];
  accessories: number[];
  premium_offer: string;
  premium_offer_expiration: string;
  premium_offer_sent: string;
  allow_astronomy_ads: boolean;
  inactive_account_reminder_sent: string;
  astrobin_index: number;
  followers: number;
  premium_counter: number;
}

@Injectable({
  providedIn: "root"
})
export class CommonApiAdaptorService extends BaseService {
  permissionFromBackend(permission: BackendPermissionInterface): PermissionInterface {
    return {
      id: permission.id,
      name: permission.name,
      codeName: permission.codename,
      contentType: permission.content_type
    };
  }

  groupFromBackend(group: BackendGroupInterface): GroupInterface {
    return {
      id: group.id,
      name: group.name,
      permissions: group.permissions.map(permission => this.permissionFromBackend(permission))
    };
  }

  userFromBackend(user: BackendUserInterface): UserInterface {
    return {
      id: user.id,
      userProfile: user.userprofile,
      username: user.username,
      firstName: user.first_name,
      avatar: user.avatar,
      lastLogin: new Date(user.last_login),
      dateJoined: new Date(user.date_joined),
      isSuperUser: user.is_superuser,
      isStaff: user.is_staff,
      isActive: user.is_active,
      groups: user.groups.map(group => this.groupFromBackend(group)),
      userPermissions: user.user_permissions.map(permission => this.permissionFromBackend(permission))
    };
  }

  userProfileFromBackend(userProfile: BackendUserProfileInterface): UserProfileInterface {
    return {
      id: userProfile.id,
      deleted: new Date(userProfile.deleted),
      updated: new Date(userProfile.updated),
      realName: userProfile.real_name,
      website: userProfile.website,
      job: userProfile.job,
      hobbies: userProfile.hobbies,
      timezone: userProfile.timezone,
      about: userProfile.about,
      companyName: userProfile.company_name,
      companyDescription: userProfile.company_description,
      companyWebsite: userProfile.company_website,
      retailerCountry: userProfile.retailer_country,
      avatar: userProfile.avatar,
      excludeFromCompetition: userProfile.exclude_from_competitions,
      defaultFrontPageSection: userProfile.default_frontpage_section,
      defaultGallerySorting: userProfile.default_gallery_sorting,
      defaultLicense: userProfile.default_license,
      defaultWatermark: userProfile.default_watermark,
      defaultWatermarkOpacity: userProfile.default_watermark_opacity,
      defaultWatermarkPosition: userProfile.default_watermark_position,
      defaultWatermarkSize: userProfile.default_watermark_size,
      defaultWatermarkText: userProfile.default_watermark_text,
      acceptTos: userProfile.accept_tos,
      receiveNewsletter: userProfile.receive_newsletter,
      receiveImportantCommunications: userProfile.receive_important_communications,
      receiveMarketingAndCommercialMaterial: userProfile.receive_marketing_and_commercial_material,
      language: userProfile.language,
      seenRealName: userProfile.seen_realname,
      seenEmailPermissions: userProfile.seen_email_permissions,
      signature: userProfile.signature,
      signatureHtml: userProfile.signature_html,
      showSignatures: userProfile.show_signatures,
      postCount: userProfile.post_count,
      autoSubscribe: userProfile.autosubscribe,
      receiveForumEmails: userProfile.receive_forum_emails,
      user: userProfile.user,
      telescopes: userProfile.telescopes,
      mounts: userProfile.mounts,
      cameras: userProfile.cameras,
      focalReducers: userProfile.focal_reducers,
      software: userProfile.software,
      filters: userProfile.filters,
      accessories: userProfile.accessories,
      premiumOffer: userProfile.premium_offer,
      premiumOfferExpiration: new Date(userProfile.premium_offer_expiration),
      premiumOfferSent: new Date(userProfile.premium_offer_sent),
      allowAstronomyAds: userProfile.allow_astronomy_ads,
      inactiveAccountReminderSent: new Date(userProfile.inactive_account_reminder_sent),
      astroBinIndex: userProfile.astrobin_index,
      followers: userProfile.followers,
      premiumCounter: userProfile.premium_counter
    };
  }
}

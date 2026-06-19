import iconLightbulb from '../assets/icons/icon-lightbulb.png';
import iconShield from '../assets/icons/icon-shield.png';
import iconHeart from '../assets/icons/icon-heart.png';
import iconDownload from '../assets/icons/icon-download.png';
import iconCheck from '../assets/icons/icon-check.png';
import iconCross from '../assets/icons/icon-cross.png';
import iconStar from '../assets/icons/icon-star.png';
import iconFolderEmpty from '../assets/icons/icon-folder-empty.png';
import iconParty from '../assets/icons/icon-party.png';
import iconWarning from '../assets/icons/icon-warning.png';
import iconThinking from '../assets/icons/icon-thinking.png';
import iconCoffeeEmpty from '../assets/icons/icon-coffee-empty.png';
import iconUserEmpty from '../assets/icons/icon-user-empty.png';
import iconClipboardEmpty from '../assets/icons/icon-clipboard-empty.png';

export const ICONS = {
  lightbulb: iconLightbulb,
  shield: iconShield,
  heart: iconHeart,
  download: iconDownload,
  check: iconCheck,
  cross: iconCross,
  star: iconStar,
  folderEmpty: iconFolderEmpty,
  party: iconParty,
  warning: iconWarning,
  thinking: iconThinking,
  coffeeEmpty: iconCoffeeEmpty,
  userEmpty: iconUserEmpty,
  clipboardEmpty: iconClipboardEmpty,
};

export default function AppIcon({ name, size = 20, className = '', alt = '' }) {
  const src = ICONS[name];
  if (!src) return null;

  return (
    <img
      src={src}
      alt={alt || name}
      width={size}
      height={size}
      className={`inline-block object-contain shrink-0 ${className}`}
      draggable={false}
    />
  );
}

/** Ligne de liste forfait avec icône check / cross / star */
export function PlanFeature({ icon = 'check', children, className = '' }) {
  const sizes = { check: 14, cross: 14, star: 14 };
  return (
    <li className={`flex items-start gap-2 ${className}`}>
      <AppIcon name={icon} size={sizes[icon] || 14} className="mt-0.5" />
      <span>{children}</span>
    </li>
  );
}

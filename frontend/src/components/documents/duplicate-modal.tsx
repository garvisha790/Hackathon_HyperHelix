import React from "react";
import { AlertTriangle } from "lucide-react";
import { formatDate } from "@/lib/utils";

interface ExistingDocument {
  id: string;
  file_name: string;
  status: string;
  created_at: string;
}

interface DuplicateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onReplace: () => void;
  onKeepBoth: () => void;
  existingDocument: ExistingDocument | null;
  newFileName: string;
}

export const DuplicateModal: React.FC<DuplicateModalProps> = ({
  isOpen,
  onClose,
  onReplace,
  onKeepBoth,
  existingDocument,
  newFileName,
}) => {
  if (!isOpen || !existingDocument) return null;

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      UPLOADED: "bg-blue-100 text-blue-800",
      PROCESSING: "bg-yellow-100 text-yellow-800",
      VALIDATED: "bg-green-100 text-green-800",
      FAILED: "bg-red-100 text-red-800",
      COMPLETED: "bg-green-100 text-green-800",
    };
    return (
      <span
        className={`px-2 py-1 rounded-full text-xs font-medium ${
          colors[status] || "bg-gray-100 text-gray-800"
        }`}
      >
        {status}
      </span>
    );
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          {/* Header */}
          <div className="flex items-start mb-4">
            <div className="flex-shrink-0">
              <AlertTriangle className="h-6 w-6 text-amber-600" />
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-lg font-semibold text-gray-900">
                Duplicate Document Detected
              </h3>
              <p className="mt-2 text-sm text-gray-600">
                A document with the same name already exists in your system.
              </p>
            </div>
          </div>

          {/* Existing Document Info */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
            <div className="text-sm">
              <div className="font-medium text-gray-900 mb-2">
                Existing Document:
              </div>
              <div className="space-y-1 text-gray-700">
                <div className="flex items-center justify-between">
                  <span className="font-medium">Name:</span>
                  <span className="text-gray-900 truncate ml-2 max-w-xs">
                    {existingDocument.file_name}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-medium">Status:</span>
                  {getStatusBadge(existingDocument.status)}
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-medium">Uploaded:</span>
                  <span>{formatDate(existingDocument.created_at)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* New Document Info */}
          <div className="text-sm text-gray-600 mb-6">
            <span className="font-medium">New file:</span> {newFileName}
          </div>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={onKeepBoth}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium transition-colors"
            >
              Keep Both
            </button>
            <button
              onClick={onReplace}
              className="flex-1 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 font-medium transition-colors"
            >
              Replace Existing
            </button>
          </div>
        </div>
      </div>
    </>
  );
};
